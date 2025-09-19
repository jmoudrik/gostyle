from celery.task import task
from celery.exceptions import SoftTimeLimitExceeded
from celery.signals import worker_process_init, setup_logging, beat_init

import os
import os.path
import time
import string
import json
import itertools
import types
import logging

import mylog
import logging_facilities
import config
import godb
import utils

import orange_utils
from orange_utils import str2dan_kyu, get_relevant_pros, str_regression, style_regression, is_style_unreliable
from archive_utils import extract_archive, get_kgs_games
from recommend import generate_recommendations

def worker_init(*args, **kwargs):
    mylog.init_logging_celery_worker()
    
    orange_utils.INIT_str_pathway()
    orange_utils.INIT_style_pathway()
    
    godb.db_cache.init_cache(filename=':memory:',
                             expires=120)

    
setup_logging.connect(mylog.init_logging_celery_root)
worker_process_init.connect(worker_init)
#beat_init.connect(mylog.init_logging_celerybeat)

@task(max_retries=0)
def fetch_archives(argd):
    fetch_archives.task_id = fetch_archives.request.id
    if not fetch_archives.task_id:
        fetch_archives.task_id = 'task-id-pokus_fetch'
        
    logging_facilities.update_context(context=fetch_archives.task_id)
    
    def set_status(status):
        logging.info("Set status: %s"%status)
        fetch_archives.update_state(state="PROGRESS", meta=status)
        
    logging.info("argd=%s"%argd)
        
    ## generate content
    gamedir = None
    
    if 'user_file' in argd:
        set_status("Extracting archive")
        gamedir = extract_archive(fetch_archives.task_id, argd['user_file'], config.GAMES_LIMIT)
    elif 'user_kgs' in argd:
        if not argd['user_kgs']:
            raise RuntimeError("No data supplied.")
        set_status("Fetching KGS archives. This might actually take some time for some players"
                   ", since we do not want to exceed the KGS quota.")
        gamedir = get_kgs_games(fetch_archives.task_id, argd['user_kgs'], config.GAMES_LIMIT)
    elif 'user_gokifu' in argd:
        raise ValueError("Sorry gokifu is not supported yet.")
        #set_status("Fetching gokifu archives")
        #gamedir = get_gokifu_games(fetch_archives.task_id, argd['user_gokifu'], config.GAMES_LIMIT)
        
    logging.info("Games directory: '%s'"%gamedir)
    
    if not gamedir:
        raise RuntimeError("No games uploaded.")
    
    return gamedir
    
@task(max_retries=0)
def process_games(gamedir):
    process_games.task_id = process_games.request.id
    if not process_games.task_id:
        process_games.task_id = 'task-id-pokus_process'
        
    logging_facilities.update_context(context=process_games.task_id)
    
    def set_status(status):
        logging.info("Set status: %s"%status)
        process_games.update_state(state="PROGRESS", meta=status)
        
    html_target_suffix = config.OUTPUT_DIR_HTML_W + process_games.task_id
    html_res_dir = config.OUTPUT_DIR_HTML + html_target_suffix
    if not os.path.isdir(html_res_dir):
        os.makedirs(html_res_dir)
        
    set_status("Scanning the games")
    s = godb.my_session.my_session_maker(':memory:')
    gl = s.godb_add_dir_as_gamelist(gamedir)
    s.add(gl)
    s.commit()
    
    if not len(gl):
        raise RuntimeError("No games uploaded.")
    
    
    # most frequent player
    player, _ = max(itertools.groupby(sorted(gl.iter_players())),
                    key=lambda (k, g): len(list(g)) )
    
    osl = godb.models.OneSideList( player.name,
                                   player.iter_one_side_associations() )
    
    set_status("Processing the games, this might take a while...")
    str_pat, strength = str_regression(osl, html_res_dir)
    
    #{'ag': { 'val' : 10, 'sigma' : 10192, 'pic' : 'out.png' } }
    style = style_regression(osl, html_res_dir)
    similar_pros, distant_pros = get_relevant_pros(style)
    
    res = {
        'str' : str2dan_kyu(strength), 
	'similar_pros' : similar_pros,
	'distant_pros' : distant_pros,
	'sample_size' : len(osl),
	'style_unreliable' : is_style_unreliable(strength, style),
	'unreliable' : len(osl) < 15,
	'task_id' : process_games.task_id,
	'name_in_games' : player.name, 
    }
    
    res.update(style)
    
    sub = {'SUB_res' : json.dumps(res),
           'SUB_recommendations' : generate_recommendations(strength['val']),
           'SUB_kgs_timespan' : utils.get_timespan(osl),
           'SUB_str_pat' : str_pat,
           'SUB_games' : utils.osl_to_html(osl, player).encode('utf-8') }
    
    
    ## finalize
    
    # clean up
    set_status("Cleaning up.")
    godb.db_cache.delete_expired()
    
    if not config.RUNNING_LOCALLY:
        utils.remove_old_files(config.OUTPUT_PAT_GODB, config.DELETE_TMP_FILES)
    
    set_status("Finalizing.")
    # load template
    with open( os.path.join(config.TEMPLATE_DIR, 'result.html'),  'r' ) as ftempl:
        template = string.Template(ftempl.read())
        
    # write the output
    out_filename = os.path.join(html_res_dir, 'index.html')
    
    with open(out_filename, 'w') as fout:
        fout.write(template.safe_substitute(sub))
    
    logging.info("Result stored in: '%s'"%(html_target_suffix))
    
    return html_target_suffix
        
@task(ignore_result=True, name="task_collect_garbage")
def collect_garbage(tid):
    pass

@task
def task_nop(*args):
    time.sleep(20)
    pass

if __name__ == '__main__':
    
    from godb import db_cache
    
    db_cache.init_cache(filename=':memory:', log=True)

    #print process_games({'user_file': 'arch.tar.bz2'})
    print process_games('')
