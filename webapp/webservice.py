#!/usr/bin/python

import web
import logging
import time
import json
import cgi
import mylog
import os


from threading import RLock

mylog.init_logging_main()
logging.info(os.getcwd())

import config

cgi.maxlen = config.UPLOAD_ARCHIVE_SIZE_LIMIT

from misc import log_exceptions, provide_callback,  unique_hash,  parseq
import celery_tasks

### Url mappings

urls = (
    #'/',  'Hello', 
    #'/get_status',  'GetStatus', 
    #'/submit', 'Submit',
    #'/submit-correction', 'SubmitCorrection',
    '/webapp-w/',  'Hello', 
    '/webapp-w/get_status',  'GetStatus', 
    '/webapp-w/submit', 'Submit',
    '/webapp-w/submit-correction', 'SubmitCorrection',
)

# dicts for query parsing
# key : (default value, convert fc)
GETPD = {
    "id" : (None, str),
    }

dlock = RLock()
celery_tasks_res = {}

class Hello:
    def GET(self):
        return "<h1>hello</h1>"
    
# we do not want to leak memory over time by growing the dicts above...
# used as a decorator hooked to HTTP requests
def collect_garbage(f):
    def g(*args,**kwargs):
        t = time.time() 
        
        with dlock:
            for tid, (task, t_start, task_type) in celery_tasks_res.items():
                diff = t - t_start  
                if diff > config.SERVER_COLLECT_GARBAGE_DELAY:
                    logging.info("Collecting task garbage: " + tid)
                    # remove from dict
                    del celery_tasks_res[tid]

        return f(*args, **kwargs)
    return g

class SubmitCorrection:
    @log_exceptions
    def POST(self):
        ## informace o tom ktery task to byl jsou zapsany v souboru
        name =  os.path.join(config.CORRECTIONS_DIR, unique_hash())
        with open(name,  'w') as fout:
            fout.write( web.data() )
        
        logging.info("Correction submit from '%s' -> written to '%s'."%(str(web.ctx.ip), name))
        return ''
    
class Submit:
    @log_exceptions
    @collect_garbage
    def POST(self):
        logging.info("Submit from '%s'"%(str(web.ctx.ip) ))
        
        try:
            x = web.input()
        except ValueError:
            logging.info("Archive too big.")
            return "Archive file is too big. Limit is 512 kB."
        
        argd = {}
        if x['user_file']:
            fn =  os.path.join(config.UPLOAD_DIR, unique_hash())
            with open(fn, 'w') as fout:
                fout.write(x['user_file'])
            argd['user_file'] = fn
            logging.info("Data written to %s."%fn)
        for key in ['user_kgs',  'user_gokifu']:
            if key in x:
                argd[key] = x[key]
	        logging.info("got %s = %s"%(key, x[key]))
                
        q = 'default'
        if argd.get('user_kgs', None) and not argd.get('user_file', None):
            q = 'kgs_queue'
        
        task = celery_tasks.fetch_archives.apply_async(args=[argd], queue=q)
        #task = celery_tasks.task_nop.delay(argd)
            
        with dlock:
            celery_tasks_res[task.task_id] = (task,  time.time(), ("fetch",))
        
        raise web.seeother('/check_status.html#?id=%s'%task.task_id)

class GetStatus:
    @log_exceptions
    @provide_callback
    def GET(self):
        d = parseq(web.ctx.query, GETPD)
        
        with dlock:
            tup = celery_tasks_res.get(d['id'], None)
        
        ret = {}
        
        if not tup:
            ret['state'] = "FAILURE"
            ret['result'] = "Wrong job id."
            logging.info(d['id'])
        else:
            task, start_time, task_type = tup
            
            status = task.status
            result = task.result

            if status == "STARTED":
                ret['state'] = "WORKING"
                ret['result'] = "Job started."

            elif status == "PENDING":
                ret['state'] = "PENDING"
                ret['result'] = "The task is waiting for processing."

            elif status == "REVOKED":
                ret['state'] = "FAILURE"
                ret['result'] = "Task revoked."

            elif status == "RETRY":
                ret['state'] = "WORKING"
                ret['result'] = "Retrying."

            elif status == "SUCCESS":
                if task_type[0] == 'fetch':
                    with dlock:
                        sub_task = celery_tasks.process_games.apply_async(args=[result], queue='default')
                        celery_tasks_res[sub_task.task_id] = (sub_task, time.time(), ("process",))
                        task_type = ("spawned",  sub_task.task_id)
                        celery_tasks_res[task.task_id] = (task, start_time, task_type)
                        
                    logging.info("Task '%s' spawned '%s'"%(task.task_id, sub_task.task_id))
                    
                if task_type[0] == "spawned":
                    ret['state'] = "REDIRECT"
                    ret['result'] = str(task_type[1])
                else:
                    ret['state'] = "SUCCESS"
                    ret['result'] = str(result)

            elif status == "PROGRESS":
                ret['state'] = "WORKING"
                ret['result'] = str(result)

            elif status == "FAILURE":
                ret['state'] = "FAILURE"
                ret['result'] = str(result)
                
            else:
                ret['state'] = "FAILURE"
                ret['result'] = "Internal unspecified error."
        
        """
        with dlock:
            logging.info("get_status\n\tfor: %s,\n\tret: %s\n\tres: %s"%(
                        d['id'],
                        repr(ret),
                        celery_tasks_res
                    ))
        """
        web.header('Content-Type', 'application/json')
        return json.dumps(ret)
    
#
#   Run...
#

app = web.application(urls, globals())
web.config.debug = False

if __name__ == '__main__':
    app.run()
