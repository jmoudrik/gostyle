import logging
from logging import handlers
import Orange
import urllib2

from models import *
from game_to_vec import *

from pokus import get_pathway
from my_session import my_session_maker
import cl_strength, cl_style, cl_year,  cl_strength_by_player
import db_cache
import timer
import kgs
import rank
            

def main():
    ## init stuff
    logger = logging.getLogger()
    logger.setLevel(logging.WARNING)
    t =  timer.Timer()
    s = my_session_maker(filename='GODB_kgs_wide.db')
    db_cache.init_cache(filename='/media/ramdisk/CACHE_kgs_wide.db')

    ## prepare the processing pathway
    KGS = s.query(GameList).filter(GameList.name == 'KGS wide').one()
    SPATIAL_dict_data = KGS
    
    dm_name = cl_strength_by_player.get_datamap_name(KGS)
    DATAMAP = s.query(DataMap).filter(DataMap.name == dm_name).one()
    ALL_PAT_OSL = s.query(OneSideList).filter(OneSideList.name == dm_name + ' - OSL merged, 30% sample').one()
    
    vg_osl = get_pathway(SPATIAL_dict_data, ALL_PAT_OSL, t)
    
    ## train the classifier
    TRAIN_DATA = 'TABS/KGS_wide_by_player_60/results.tab'
    train_table = Orange.data.Table(TRAIN_DATA)
    
    learner = Orange.classification.knn.kNNLearner()
    learner.k = 4
    
    learner = Orange.regression.pls.PLSRegressionLearner(name='pls')
    
    classifier = learner(train_table)
    
    import random
    #random.seed(3)
    player_name =  'bronislav'
    ##random.seed(16)
    player_name =  'Lukan'
    
    for month in xrange(3, 13):
        ## 
        #dire = 'TMP2/archive%d' % (random.randint(1, 10e6))
        dire = 'TMP2/%smonth-%d/' % (player_name, month)
        year = 2012
        #month = 9
        
        try:
            kgs.get_archive(dire, player_name, year, month)
            pass
        except urllib2.URLError:
            continue
        
        gl = s.godb_add_dir_as_gamelist(dire)
        osl = OneSideList(player_name)
        for game in gl:
            if ( 0 != int(game.sgf_header.get('HA', 0)) or
                19 != int(game.sgf_header.get('SZ', 0)) ):
                   continue
                   
            osl.add(game, color=PLAYER_COLOR_BLACK)
            osl.add(game, color=PLAYER_COLOR_WHITE)
            continue
        
            if game.black.name == player_name:
                osl.add(game, color=PLAYER_COLOR_BLACK)
            else:
                osl.add(game, color=PLAYER_COLOR_WHITE)
        
        if len(osl) == 0:
            continue
        
        logging.info("Taken %d non handicap and 19x19 games."%(len(osl)))
        logging.info("Processing games..")
        pattern_vector = vg_osl(osl)
        logging.info("Finished.")
        #return pattern_vector 
        
        i = Orange.data.Instance(train_table.domain, list(pattern_vector) + [666])
        rankf = classifier(i)
        
        print "Games from month %d: %d games, %s, %s" % (
            month, len(osl), rankf, rank.Rank.from_key(rankf)
        )
        
        s.rollback()

if __name__ == '__main__':
    print main()
