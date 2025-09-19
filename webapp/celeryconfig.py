import config

#BROKER_TRANSPORT = "sqlalchemy"

#filebase = config.SERVER_ROOT_DIR + "/data/celerydb.sqlite"

filebase = "/dev/shm/WEBAPP.celerydb.sqlite"

BROKER_URL = 'sqla+sqlite:///' + filebase

BROKER_TRANSPORT_OPTIONS = { 'connect_args' : {'timeout': 10} }

#CELERY_RESULT_DBURI = BROKER_HOST
CELERY_RESULT_BACKEND = 'db+sqlite:///' + filebase
#CELERY_RESULT_ENGINE_OPTIONS = {'echo': True}

CELERYD_HIJACK_ROOT_LOGGER = False

CELERY_DISABLE_RATE_LIMITS = True

CELERY_IMPORTS = ("celery_tasks", )

#CELERYD_CONCURRENCY = 2 #if serverconfig.RUN_LOCALLY else 4

# ten minutes
CELERYD_TASK_TIME_LIMIT = 600
CELERYD_TASK_SOFT_TIME_LIMIT = CELERYD_TASK_TIME_LIMIT - 10

CELERY_CREATE_MISSING_QUEUES = True
CELERY_ROUTES = {
"task.kgs": { "queue": "kgs_queue", }
}


from celery.schedules import crontab
from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    #"morning-restart-unoconv": {
    #    "task": "celery_tasks.restart_unoconv_listener",
    #    "schedule": crontab(hour=3, minute=00),
    #},
}
