#!/usr/bin/env python2

import sys
import os
from datetime import datetime, timedelta, date
import shutil

def get_day_in_last_month(today):
    day_in_last_month = today - timedelta(days=28)
    if today.day >= 29:
        day_in_last_month = today - timedelta(days=31)
        
    return day_in_last_month

LOGFILE = '/opt/gostyle/webapp/log'
#LOGFILE = './log'

today = datetime.today()
day_in_last_month = get_day_in_last_month(today)

def remove_old_kgs_files(cache_dir, year, month):
    for to_del in [ os.path.join(cache_dir, 'ARCHIVES', str(year), str(month)),
                    os.path.join(cache_dir, 'LIST', str(year), str(month))
                    ]:
        if os.path.isdir(to_del):
            shutil.rmtree(to_del)

if __name__ == '__main__':
    ## only run on first of month
    run_today = today.day == 1
    
    if len(sys.argv) == 2:
        directory = sys.argv[1]
    # or if forced
    elif len(sys.argv) == 3 and sys.argv[2] == 'FORCE_TODAY':
        directory = sys.argv[1]
        run_today = True
    else:
        print >> sys.stderr, """Usage: %s DIRECTORY [FORCE_TODAY]
Cleans kgs cache DIRECTORY from last month. Runs on 1. of each month, unless FORCE_TODAY
specified.
""" % (sys.argv[0], )
        sys.exit(1)
        
    if run_today:
        with open(LOGFILE, 'a') as flog:
            flog.write("%s -- KGS CLEAN -- : RUNNING, removing files from '%s' from last month (%s of %s).\n" % (
                today, directory,
                day_in_last_month.month,
                day_in_last_month.year))
            
        remove_old_kgs_files(directory, day_in_last_month.year, day_in_last_month.month)
