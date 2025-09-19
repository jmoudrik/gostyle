import os
import shutil
import random
import signal
import subprocess
import re
import calendar

from kgs import KGS, KGSNotFound
import config
import sgf_load

class Alarm(Exception):
    pass

def alarm_handler(signum, frame):
    raise Alarm


kgs_f = KGS(os.path.join(config.OUTPUT_DIR, 'KGS' ))

class GameDirs:
    def __init__(self, limit, basedir):
        if not os.path.isdir(basedir):
            os.makedirs(basedir)
        self.basedir = basedir
        self.limit = limit
        self.filelist = []
        self.dir2del = []
        
    def has_enough(self):
        return len(self.filelist) >= self.limit
    
    def move_and_delete(self):
        cnt = 0
        sample = self.filelist
        if len(self.filelist) > self.limit:
            sample = random.sample(sample, self.limit)
            
        for filename in sample:
            cnt += 1
            new_file = os.path.join(self.basedir,  "%s.sgf" % (cnt) )
            shutil.move(filename, new_file)
        
        for old_dir in self.dir2del:
            shutil.rmtree(old_dir)
            
        return self.basedir
        
    def add(self, directory):
        self.dir2del.append(directory)
    
        count = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for fn in filenames:
                if fn[-4:] != '.sgf':
                    continue
                
                filename = os.path.join(dirpath, fn)
                
                rm = False
                    
                try:
                    header = sgf_load.load_sgf_file_headers(filename)[0]
                except (sgf_load.ParseError, IndexError) :
                    rm = True
                
            
                if not rm:
                    try:
                        rm = rm | (0 != int(header.get('HA', 0)))
                        rm = rm | (19 != int(header.get('SZ', 0)))
                    except ValueError:
                        rm = True
                
                if not rm:
                    self.filelist.append(filename)
                    count += 1
        return count
        
def extract_archive(task_id, user_file, limit):
    extract_to_dir = os.path.join(config.OUTPUT_DIR, 'EXTRACT', task_id)
    if not os.path.isdir(extract_to_dir):
        os.makedirs(extract_to_dir)
        
    archive_name = 'archive'
    shutil.copy(user_file, os.path.join(extract_to_dir, archive_name))
    
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(5)  # 5 secs
    try:
        retcode = subprocess.call("""
        cd %s
        dtrx -n '%s'
        """%(extract_to_dir, archive_name), shell=True )
        
        signal.alarm(0)
    except Alarm:
        retcode = 666
    
    if retcode:
        raise RuntimeError('Unable to extract the archive.')
    
    dirs = GameDirs(limit, os.path.join(config.OUTPUT_DIR, 'GAMES', task_id))
    dirs.add(extract_to_dir)
    
    return dirs.move_and_delete()

def get_kgs_games(task_id, user_kgs, limit):
    if not re.match('^[0-9a-zA-Z]*$', user_kgs):
        raise ValueError("Invalid characters in the player's name '%s'."%user_kgs)
  
    dirs = GameDirs(limit, os.path.join(config.OUTPUT_DIR, 'GAMES', task_id))
    
    years_spent = []
    for year, month in reversed(kgs_f.list_active(user_kgs, force_this_month=True)):
        try:
            count = dirs.add(kgs_f.fetch_archive_and_extract(user_kgs, year, month))
        except KGSNotFound:
            continue
        
        years_spent.append((year, month, count))
        
        if dirs.has_enough():
            break
        
    return dirs.move_and_delete()

def get_gokifu_games(user_gokifu, limit):
    pass

def kgs_time_span2text(years_spent):
    if not years_spent:
        return ''
        
    def get_month(tup):
        year, month, num = tup
        return "%s of %s" % (calendar.month_name[int(month)], year)
        
    s = sorted(years_spent)
    if len(s) == 1:
        return ", from %s" % get_month(s[0])
    
    return ", spanning from %s to %s" % ( get_month(s[0]), get_month(s[-1]))

if __name__ == '__main__':
    #print extract_archive('123',  './arch.tar.bz2', 20)
    
    y = kgs_f.list_active('Boidhre')
    
    print y
    
    
    
    