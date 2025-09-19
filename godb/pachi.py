import logging
import subprocess
from subprocess import PIPE

import os
from os import remove
from os.path import abspath

import sys
import shutil
import re
from collections import namedtuple

import misc
import utils
from utils import ResultFile
from db_cache import declare_pure_function, cache_result
import models
from models import PLAYER_COLOR_BLACK, PLAYER_COLOR_WHITE

from config import PACHI_DIR

PACHI_SPATIAL_DICT = os.path.join(PACHI_DIR, 'patterns.spat')

class Pattern:
    def __init__(self, pattern=None, fpairs=None):
        if pattern != None:
            match = re.match('^\((.*)\) *$', pattern)
            if not match:
                    raise RuntimeError("Pattern format wrong: '%s'"%pattern)
            
            # (capture:104 border:6 atari:0 atari:0 cont:1 s:2620)
            pattern = match.group(1)
        
            self.fpairs = []
            for featpair in pattern.split():
                feat, payload = featpair.split(':')        
                self.fpairs.append((feat, int(payload)))
        elif fpairs != None:
            self.fpairs = fpairs
        else:
            raise RuntimeError("Pattern unspecified...")
    
    def reduce(self, filterfc):
        fpairs = [ (f, p) for f, p in self if filterfc(f, p) ]
        return Pattern(fpairs=fpairs)
    
    def iter_feature_payloads(self, feature):
        for f, p in self:
            if f == feature:
                yield p
    
    def first_payload(self, feature):
        return self.iter_feature_payloads(feature).next()

    def has_feature(self, feature):
        for f, p in self:
            if f == feature:
                return True
        return False
        
    def __iter__(self):
        return iter(self.fpairs)
            
    def __str__(self):
        return "(%s)"%( ' '.join( "%s:%s"%(feat, payload) for feat, payload in self ) )

class IllegalMove(Exception):
    pass

@cache_result
@declare_pure_function
def generate_spatial_dictionary(game_list, spatmin=4, patargs='', check_size=329):
    """
    Generates pachi spatial dictionary from games in the @gamelist.
    
    @check_size specifies min spatial dict size, if the filesize is below, raise runtime err.
    Set this to 0 to disable the check. (328 is the size of empty spatial dict header)
    """
    logging.info("Generating spatial dictionary from %s"%(repr(game_list)))
    
    # pachi does not handle larger number of handicap stones than 9
    without_large_handi = filter( lambda g : int(g.sgf_header.get('HA',0)) <= 9, game_list.games )
    l_old, l_new =  len(game_list.games), len(without_large_handi)
    if l_old != l_new:
        logging.warn("The spatial dictionary list contains %d games with # of handicap stones >= 10. Skipping those."%(
                l_old - l_new,))
        
    games = '\n'.join([ abspath(game.sgf_file) for game in without_large_handi ])
    
    spatial_dict = utils.get_output_resultfile('.spat')
    assert not spatial_dict.exists()
    
    script="""
    cd %s
    SPATMIN='%s' SPATIAL_DICT_FILE='%s' PATARGS='%s' tools/pattern_spatial_gen.sh -"""%(
        PACHI_DIR, spatmin, abspath(spatial_dict.filename), patargs)
    
    #with open("tmp_script", 'w') as tmp:
    #   tmp.write(script)
    
    p = subprocess.Popen(script, shell=True, stdin=PIPE)    
    o = p.communicate(input=games.encode('utf-8'))
    #if stderr:
    #    logging.warn("subprocess pattern_spatial_gen stderr:\n%s"%(stderr,))
    if p.returncode:
        raise RuntimeError("Child process `pattern_spatial_gen` failed, exitcode %d."%(p.returncode,))
    if check_size and os.stat(spatial_dict.filename).st_size <= check_size:
        raise RuntimeError("Spatial dict is empty. Probably an uncaught error in subprocess.")
    
    logging.info("Returning spatial dictionary %s"%(repr(spatial_dict)))
    return spatial_dict


@cache_result
@declare_pure_function
def scan_raw_patterns(game, spatial_dict=None, patargs='', skip_empty=True):
    """
    For a @game, returns list of pairs (player_color, pattern) for each move.
    The pachi should be compiled to output all the features.
    """
    if spatial_dict == None:
        if 'xspat=0' not in patargs.split(','):
            raise RuntimeError("Spatial dict not specified, though the spatial features are not turned off.")
        spatial_str=""
    else:
        assert spatial_dict.exists(warn=True)
        spatial_str="spatial_dict_filename=%s"%(abspath(spatial_dict.filename))
        
    gtpscript="""
    cd %s
    
    ./tools/sgf2gtp.py --stdout '%s'
    """%(PACHI_DIR, abspath(game.sgf_file) )
    gtpstream = utils.check_output(gtpscript, shell=True)
    
    script = """
    cd %s
    ./pachi -d 0 -e patternscan '%s'
    """%( PACHI_DIR, ','.join(misc.filter_null([spatial_str, patargs])) )
    
    p = subprocess.Popen(script, shell=True, stdout=PIPE, stdin=PIPE, stderr=PIPE)    
    
    pats, stderr = p.communicate(input=gtpstream)
    if stderr:
        logging.warn("subprocess pachi:\n\tSCRIPT:\n%s\n\tSTDERR\n%s"%(script, stderr))
        
    if p.returncode:
        raise RuntimeError("Child process `pachi` failed, exitcode %d."%(p.returncode,))
    
    lg = filter( lambda x : x, gtpstream.split('\n'))
    lp = pats.split('\n')
    
    # ? illegal move
    wrong = filter( lambda x: re.search('^\? ',x), lp)
    if wrong:
        raise models.ProcessingError("Illegal move")
        #raise IllegalMove() #"In game %s"%game)
    
    # filter only lines beginning with =
    lp = filter( lambda x: re.search('^= ',x), lp)
    # remove '= ' from beginning
    lp = map( lambda x: re.sub('^= ', '', x), lp) 
    
    # the command list and the pattern list should be aligned
    #  - each gtp command emits one line of patterns from pachi
    assert len(lg) == len(lp)
    gtp_pat = zip(lg, lp)
    
    # keep pairs that contain something else than space in pattern
    #  - discards boardsize, handi, komi, ... that emit nothing ('= ')
    gtp_pat = filter( lambda t: re.search('\S', t[1]), gtp_pat)
    
    # filter out other gtp commands than play
    #  - discards e.g. 'fixed_handicap' command and the resulting positions
    #    of handicap stones
    gtp_pat = filter( lambda t: re.search('^play', t[0]), gtp_pat)
    
    # remove empty [()]
    if skip_empty:
        gtp_pat = filter( lambda (gtp, pat) : len(pat) != 4, gtp_pat)
        
    # remove brackets enclosing features
    # [(s:99 atariescape:8)]
    # =>
    # (s:99 atariescape:8)
    def remover((gtp, pat)):
        assert pat[0] == '['
        assert pat[-1] == ']'
        return (gtp, pat[1:-1])
    gtp_pat = map(remover, gtp_pat)
        
    return [ ( PLAYER_COLOR_WHITE if gtp[5] == 'W' else PLAYER_COLOR_BLACK,
               Pattern(pat))
             for gtp, pat in gtp_pat ]

if __name__ == '__main__':
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    
    from models import Game, GameList, OneSideList, PLAYER_COLOR_BLACK, PLAYER_COLOR_WHITE
    from my_session import my_session_maker
    
    import db_cache
    db_cache.init_cache(filename=':memory:')#, cache_log=True)
    s = my_session_maker(filename=':memory:')#, echo=True)
    
    
    game = s.godb_sgf_to_game('./files/pokus_capture.sgf')     
        
    pats =  scan_raw_patterns(game,  patargs='xspat=0')    
    for c, p in pats:
        print c, p
    