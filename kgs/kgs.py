# -*- coding: utf-8 -*-

import datetime
import logging
import os
import random
import re
import subprocess
import tarfile
import tempfile
import time
import urllib2


## ! we need to ensure somewhere else that the cached archived files and cached LIST 
## from last month are deleted
        
class KGSError(RuntimeError):
    pass

class KGSNotFound(KGSError):
    pass

class KGS(object):
    """Object used to fetch data from KGS.
    
    The requests and results are cached, real requests are delayed not to
    contact the server too often.
    
    """
    def __init__(self, cache_dir, min_delay=4):
        """
        Arguments:
        cache_dir -- where to save the requests and results, created if does
                     not exist
        min_delay -- min_delay between requests in seconds
        """
        # the time of the last request
        self.last = 0
        
        # between requests
        self.min_delay = min_delay
        
        self.cache_dir = cache_dir
    
    def fetch_archive_and_extract(self, player, year, month):
        """
        Fetches games of @player, from @year and @month, extracts the archive
        and returns the directory with games.
        """
        today = datetime.datetime.today()
        
        basename = '%s-%d-%d.tar.gz' % (player, int(year), int(month))
        url = 'http://www.gokgs.com/servlet/archives/en_US/' + basename
        
        ## FETCH ARCHIVE
        archive_dir = os.path.join(self.cache_dir, 'ARCHIVES', str(year), str(month))
        if not os.path.isdir(archive_dir):
            os.makedirs(archive_dir)
            
        archive_file = os.path.join(archive_dir, basename)
        # if the file is not cached OR the cached version is not (possibly) consistent
        # (games are added if this is the current month)
        
        ## ! we need to ensure somewhere else that the cached archived files and cached LIST 
        ## from last month are deleted
        if not os.path.exists(archive_file) or (today.year == year and today.month == month):
            self.wait_min_delay()
            logging.info("Fetching KGS archive '%s'"%(url))
            try:
                try:
                    response = urllib2.urlopen(url)
                except urllib2.HTTPError as e:
                    if e.code == 404:
                        raise KGSNotFound()
                    if e.code == 503:
                        raise KGSError("KGS quota exceeded. Please download your latest games manually and upload them as an archive.")
                    raise
            except urllib2.URLError as e:
                raise KGSError("Fetching the KGS archive failed: '%s'\n  %s"%(e, url))
            finally:
                self.update_last_time()
            with open(archive_file, 'w') as archive:
                archive.write(response.read())
        
        ## EXTRACT 
        games_dir = os.path.join(self.cache_dir, 'GAMES', str(year), str(month), str(player))
        if not os.path.isdir(games_dir):
            os.makedirs(games_dir)
            
        tf = tarfile.open(archive_file)
        tf.extractall(games_dir)
        tf.close()
            
        return games_dir

    def list_games(self, player, year, month):
        """ Returns list of tuples
        [ (playername, rank), ..]
        there will be two tuples for one game even 19x19 game (white and black player) of
        @player in @year / @month
        
        only regard 19x19 even games
        """
        ret_games, ret_active, ret_games_links = self._player_archive(player, year, month)
        
        return ret_games
    
    def list_games_links(self, player, year, month):
        """ Returns list of games (links to download) played on a given month
        only regard 19x19 even games
        """
        ret_games, ret_active, ret_games_links = self._player_archive(player, year, month)
        
        return ret_this_month_games

    def list_active(self, player, force_this_month=False):
        """
        Returns list of tuples:
        [ (player, year, month), ] such that player was active in the year and month.
        
        if force_this_month option is set, add the current month even if no games were played.
        """
        today = datetime.datetime.today()
        year, month = today.year, today.month
                
        ret_games, ret_active, ret_games_links = self._player_archive(player, year, month)
        
        if ret_games_links or force_this_month:
            current = (str(year), str(month))
            if not current in ret_active:
                ret_active.append(current)
        
        if not ret_active:
            raise KGSError("Not an active user '%s'."%player)
        
        return ret_active

    def wait_min_delay(self):
        diff = time.time() - self.last
        if diff < self.min_delay:
            time.sleep(self.min_delay - diff) # + random.random())
            
    def update_last_time(self):
        self.last = time.time()

    def _player_archive(self, player, year, month, cache=True):
        assert re.match('^[0-9a-zA-Z]*$', player)
        assert int(year)
        assert int(month)
        
        tmpname = tempfile.mktemp('kgs_fetch')
        wget_file_dir = os.path.join(self.cache_dir, 'LIST', str(year), str(month))
        if not os.path.isdir(wget_file_dir):
            os.makedirs(wget_file_dir)
        wget_file = os.path.join(wget_file_dir, player)

        script= u"""
wget_outfile=%s
tmp_file=%s

[ -e $wget_outfile ] || { 

wget --user-agent="Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20100101 Firefox/15.0.1" \
 "http://www.gokgs.com/gameArchives.jsp?user=%s&year=%s&month=%s" -O $wget_outfile
 
}

[ -e $wget_outfile ] || { exit 1; }


sed 's/<tr>/\\n&/g' $wget_outfile > $tmp_file

# even games in the month
sed '/<td>19×19[ ]\?<\/td>/!d' $tmp_file > ${tmp_file}.games
sed -i 's/<td>/\\n&/g' ${tmp_file}.games
cp ${tmp_file}.games ${tmp_file}.game_links

sed -i -n 's#.*<a href="gameArchives.jsp?user=\([a-zA-Z0-9]*\)">\\1 \[\([0-9]*[kd][?]\{0,1\}\)\]</a>.*#\\1 \\2#p' ${tmp_file}.games
sed -i -n 's#.*<a href="\(http://files.gokgs.com/games/[^"]*\)">[a-zA-Z]*</a>.*#\\1#p' ${tmp_file}.game_links

# active months
sed -i 's/<td>/\\n&/g' $tmp_file
sed -n -i 's#.*href="gameArchives.jsp?user=\([a-zA-Z0-9]*\)&amp;year=\([0-9]*\)&amp;month=\([0-9]*\)">.*#\\2 \\3#p' $tmp_file

        """%( wget_file, tmpname, player, year, month)
        
        #print script
        #import sys
        #sys.exit()

        # if the target file does not exist
        # = it is not cached => we will make a request
        if not os.path.exists(wget_file):
            logging.info("Fetching KGS list of active months for '%s'"%(player))
            self.wait_min_delay()
            
        retcode = subprocess.call(script, shell=True)
        self.update_last_time()
        if retcode:
            raise RuntimeError("Fetching KGS games failed.")
        
        if not cache:
            os.unlink(wget_file)
        
        ## Pairs (player, rank) for the current month
        
        with open(tmpname + '.games',  'r') as fin:
            data = fin.readlines()
        os.unlink(tmpname +'.games')

        ret_games = []
        for line in data:
            player, rank = line.rstrip().split()
            ret_games.append((player, rank))
        
        ## List of urls of downloadable games for current month
        
        with open(tmpname + '.game_links',  'r') as fin:
            ret_game_links = [ line.rstrip() for line in fin.readlines() ]
        os.unlink(tmpname +'.game_links')

        ## List of active months
        
        with open(tmpname,  'r') as fin:
            data = fin.readlines()

        os.unlink(tmpname)
        ret_active = []
        for line in data:
            lyear, lmonth =  line.rstrip().split()
            ret_active.append((lyear, lmonth))
            
        ##
        ret = (ret_games, ret_active, ret_game_links)
        return ret

if __name__ == "__main__":
    
    kgs = KGS("OUT")    
    
    today = datetime.datetime.today()
    year, month = today.year, today.month
            
    ret_games, ret_active, ret_games_links = kgs._player_archive('speteuk', year, month)
    
    print ret_games
    print
    print ret_active
    print
    print ret_games_links
    
    