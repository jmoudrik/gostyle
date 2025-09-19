import os
import logging 
import datetime

RUNNING_LOCALLY = False

OUTPUT_DIR_HTML_W = '/WAPP_RES/'
OUTPUT_DIR_HTML = '../WWW'

OUTPUT_DIR = './OUTPUT/'
UPLOAD_DIR =  os.path.join(OUTPUT_DIR, 'UPLOAD')
CORRECTIONS_DIR =  os.path.join(OUTPUT_DIR, 'CORRECTIONS')
TEMPLATE_DIR = './TEMPLATES/'
TABS_DIR = '../TABS/'
SERVER_ROOT_DIR = '.'
PICKLE_DIR = '.'

SERVER_COLLECT_GARBAGE_DELAY = 48 * 60 * 60 # 48 hours to keep in memory

## bacha
## bacha - tohle se musi menit i v godb/config
## bacha
OUTPUT_PAT_GODB = '/dev/shm/OUT_PAT'
DELETE_TMP_FILES = datetime.timedelta(seconds=120)



UPLOAD_ARCHIVE_SIZE_LIMIT = 512 * 1024 # 512 kB

GAMES_LIMIT = 40
NUM_TOP_PROS = 4
NUM_BOTTOM_PROS = 4

LOGFile = './log'
LOGGING_LEVEL = logging.INFO
LOGGING_INTO_FILE = True
LOGGING_CONSOLE = False
