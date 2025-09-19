import logging
from logging import handlers
import sys

import sqlalchemy

from models import *
import pachi
from my_session import my_session_maker
import db_cache

if __name__ == '__main__':
    s = my_session_maker(filename='GODB.db')
