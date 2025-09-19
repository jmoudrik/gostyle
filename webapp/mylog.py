import logging
from logging import handlers, Formatter

from logging_facilities import ContextAwareFormatter
import config

# main server process and threads within - xmlrpc _dispatch 
def init_logging_main():
    init_logging( id_str='== SERVER ==')
    
# each celery worker process
def init_logging_celery_root(*args, **kwargs):
    # we gotta inform about the warnings too, because the celery tasks do not return
    init_logging( id_str='_ CEL ROOT _')
    
def init_logging_celery_worker(*args, **kwargs):
    # we gotta inform about the warnings too, because the celery tasks do not return
    init_logging( id_str='  CEL WORK  ', context_aware=True)
    
def init_logging_celerybeat(*args, **kwargs):
    # we gotta inform about the warnings too, because the celery tasks do not return
    init_logging( id_str='_ CEL BEAT _')
    
def init_logging( id_str='',
                  name=None,
                  into_console=config.LOGGING_CONSOLE,
                  into_file=config.LOGGING_INTO_FILE,
                  context_aware=False ):
    
    if name == None:
        logger = logging.getLogger()
    else:
        logger = logging.getLogger(name)
        
    logger.handlers = []
    
    #formatter = ContextAwareFormatter("%(asctime)s " + id_str + " %(process)d %(thread)d : %(levelname)s : %(myrequest)s %(message)s")
    if not context_aware:
        formatter = logging.Formatter("%(asctime)s " + id_str + " %(process)d %(thread)d : %(levelname)s : %(message)s")
    else:
        formatter = ContextAwareFormatter("%(asctime)s " + id_str + " %(process)d %(thread)d : %(levelname)s : %(context)s : %(message)s")
    #formatter = logging.Formatter("%(asctimes " + id_str + " %(levelname)s : %(message)s")
    
    if into_console:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        ch.setLevel(logging.DEBUG)
        logger.addHandler(ch)
        
    if into_file:
        ch = handlers.WatchedFileHandler(config.LOGFile)
        ch.setFormatter(formatter)
        logger.setLevel(config.LOGGING_LEVEL)
        logger.addHandler(ch)
    
    logger.propagate = False
    logger.setLevel(config.LOGGING_LEVEL)
    
    logging.info("Process spawned, logging Initialized")
    #logging.debug("HANDLERS")
    #logging.debug( logger.handlers )
