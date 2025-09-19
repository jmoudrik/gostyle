import logging
import subprocess
from subprocess import PIPE

import os
import sys
from os import remove
from os.path import abspath, exists
import math

import itertools
from itertools import chain
import shutil
import re
import numpy

from db_cache import declare_pure_function, cache_result
import misc
import models
from models import BlackWhite, PLAYER_COLOR_BLACK, PLAYER_COLOR_WHITE, PLAYER_COLORS
from models import ProcessingError
from pachi import scan_raw_patterns, generate_spatial_dictionary
import pachi
from colors import * 

import utils
from utils import ResultFile, first_true_pred, get_output_resultfile, partial_right, head, partial
from config import OUTPUT_DIR

pat_file_regexp = '^\s*(\d+)\s*(.+)$'

def _make_interval_annotations(l, varname):
    """
    >>> _make_interval_annotations([10,11,12,13], 'X')
    ['X <= 10', 'X == 11', 'X == 12', 'X == 13', 'X > 13']
    >>> _make_interval_annotations([22], 'X')
    ['X <= 22', 'X > 22']
    >>> _make_interval_annotations([-1, 20], 'X')
    ['X <= -1', '-1 < X <= 20', 'X > 20']
    
    """
    if not all( misc.is_int(x) for x in l):
        raise ValueError("Interval boundaries must be a number.")
    if not l:
        return [ "any " +  varname ]
    
    prev = None
    annots = []
    for point in l + ['LAST']:
        s = varname
        # if the interval size is 1 specify the interval precisely
        if point !=  'LAST' and prev == point -  1:
            s = "%s == %d" % (s, point)
        else:
            # if not first, add left boundary
            if prev != None:
                # when we do not have right boundary as well
                if point ==  "LAST":
                    # nicer like this I guess
                    s =  "%s > %d" % (s, prev)
                else:
                    s =  "%d < %s" % (prev, s)
            # if not last, add right boundary
            if point !=  'LAST':
                s =  "%s <= %d" % (s, point)
            
        annots.append(s)
        prev = point
        
    return annots

## game -> BlackWhite( vector_black, vector_white )
class BWBdistVectorGenerator:
    def __init__(self,  by_line=[2,3,4], by_moves=[26,76]):
        self.by_line = by_line
        self.by_moves = by_moves
        
        if any( x%2 for x in by_moves ):
            logging.warn("BWDistVectorGenerator called with odd number of moves"
                         "specifying the hist size => this means that the players"
                         "wont have the same number of moves in the buckets!!")
            
        # nice annotations 
        line_annots = _make_interval_annotations(by_line, 'bdist')
        move_annots = _make_interval_annotations(by_moves, 'move')
        #line_annots = [ 'bdist <= %d'%line for line in by_line ] + [ 'bdist other']
        # move_annots = [ 'move <= %d'%move for move in by_moves ] + [ 'move other']
        
        self.annotations = [ "(bdist histogram: %s, %s)"%(m,b) for m,b in itertools.product(move_annots, line_annots) ]
        self.types = [ "continuous" ] * len(self.annotations)
        
        def leq_fac(val):
            return lambda x : x <= val
    
        # predicates giving bucket coordinate
        self.line_preds = [ leq_fac(line) for line in by_line ] + [ lambda line : True ]
        self.move_preds = [ leq_fac(movenum) for movenum in by_moves ] + [ lambda movenum : True ]
    
    def __repr__(self):
        return 'BWBdistVectorGenerator(by_line=%s, by_moves=%s)'%(repr(self.by_line),
                                                                  repr(self.by_moves))
        
    def __call__(self, game):
        """
        For a game, creates histograms of moves distance from border.
        The histograms' granularity is specified by @by_line and @by_moves parameters.
    
        The @by_moves makes different histogram for each game phase, e.g.:
            by_moves=[]         makes one histogram for whole game
            by_moves=[50]       makes two histograms, one for first 50 moves (including)
                                                    second for the rest
            by_moves=[26, 76]   makes three histograms,
                                    first  26 moves (X <=26)        ~ opening
                                    first  76 moves (26 < X <= 76)  ~ middle game
                                    rest of the game (76 < X)       ~ end game
            NOTE: of the by moves number should be even, so that we count the same
                number of moves for every player.
    
        The @by_line specifies granularity of each histogram, that is
            by_line = [3]       each hist has 2 buckets, one counts moves on first three
                                lines, second for the rest
    
            by_line = [3, 4, 5] four buckets/histogram, X <= 3, X = 4, X = 5, X > 5
        """
        # scan game, ignore spatials
        col_pat = pachi.scan_raw_patterns(game, patargs='xspat=0', skip_empty=False)
    
        buckets = {}
        for color in PLAYER_COLORS:
            # histogram
            buckets[color] = numpy.zeros(len(self.line_preds) * len(self.move_preds))
    
        for movenum, (color, pat) in enumerate(col_pat):
            try:
                bdist = pat.first_payload('border')
            except StopIteration:
                continue
    
            # X and Y coordinates
            line_bucket = first_true_pred(self.line_preds, bdist + 1) # line = bdist + 1
            move_bucket = first_true_pred(self.move_preds, movenum + 1) # movenum is counted from zero
    
            # histogram[color][X][Y] += 1
            xy = line_bucket + move_bucket * len(self.line_preds)
            buckets[color][xy] += 1
    
            #print movenum, color, bdist, "  \t",
            #print line_bucket, move_bucket,
            #print color, xy
    
        return BlackWhite(buckets[PLAYER_COLOR_BLACK], buckets[PLAYER_COLOR_WHITE])

## game -> BlackWhite( vector_black, vector_white )
class BWLocalSeqVectorGenerator:
    def __init__(self, local_threshold=5):
        self.local_threshold = local_threshold
        self.annotations = [ '(local seq < %d: sente)'%local_threshold,
                             '(local seq < %d: gote)'%local_threshold,
                             '(local seq < %d: sente - gote)'%local_threshold, ]
        self.types = [ "continuous" ] * len(self.annotations)
        
    def __repr__(self):
        return 'BWLocalSeqVectorGenerator(local_threshold=%s)'%(repr(self.local_threshold))
        
    def __call__(self, game):
        """self.local_threshold gives threshold specifiing what is considered to be a local
            sequence, moves closer (or equal) than self.local_threshold in gridcular matrix
            to each other are considered local."""
        # scan game, ignore spatials
        col_pat = pachi.scan_raw_patterns(game, patargs='xspat=0', skip_empty=False)
    
        SENTE_COOR = 0
        GOTE_COOR = 1
        DIFF_COOR = 2
    
        count = {PLAYER_COLOR_BLACK : numpy.zeros(3),
                 PLAYER_COLOR_WHITE : numpy.zeros(3)}
    
        last_local = False
        seq_start = None
        for movenum, (color, pat) in enumerate(col_pat):
            if not pat.has_feature('cont'):
                local = False
            else:
                local = pat.first_payload('cont') <= self.local_threshold
    
            # if the sequence just started
            if local and not last_local:
                # this color had to reply locally, so it was the other guy that
                # started the sequence
                seq_start = models.the_other_color(color)
    
            # if the sequence just ended
            if not local and last_local:
                # the player who started the sequence gets to continue elsewhere
                if color == seq_start:
                    count[seq_start][ SENTE_COOR ] += 1
                # if he does not <=> he lost tempo with the sequence
                else:
                    count[seq_start][ GOTE_COOR ] += 1
                    
            last_local = local
            
        for color in PLAYER_COLORS:
            cnt = count[color]
            cnt[DIFF_COOR] = cnt[SENTE_COOR] - cnt[GOTE_COOR]
    
        return BlackWhite(count[PLAYER_COLOR_BLACK], count[PLAYER_COLOR_WHITE])
    
## game -> BlackWhite( vector_black, vector_white )
class BWCaptureVectorGenerator:
    def __init__(self, by_moves=[26,76], offset=6, payload_size=4):
        """The params @offset and @payload size have to be the constants from pachi/pattern.h,
        corresponding to:
            offset =  PF_CAPTURE_COUNTSTONES        
            payload_size = CAPTURE_COUNTSTONES_PAYLOAD_SIZE
        """
        self.offset = offset
        self.payload_size = payload_size
        self.by_moves = by_moves
        
        if any( x%2 for x in by_moves ):
            logging.warn("BWCaptureVectorGenerator called with odd number of moves"
                         "specifying the hist size => this means that the players"
                         "wont have the same number of moves in the buckets!!")
            
        # nice annotations 
        capture_annots = [ 'captured', 'lost', 'difference' ]
        move_annots = _make_interval_annotations(by_moves, 'move')
        
        self.annotations = [ "(capture histogram: %s, %s)"%(m,b) for m,b in itertools.product(move_annots, capture_annots) ]
        self.types = [ "continuous" ] * len(self.annotations)
        
        def leq_fac(val):
            return lambda x : x <= val
    
        # predicates giving bucket coordinate
        self.move_preds = [ leq_fac(move) for move in by_moves ] + [ lambda movenum : True ]
        
    def __repr__(self):
        args =  map(repr, [self.by_moves,  self.offset,  self.payload_size])
        return 'BWCaptureVectorGenerator(by_moves=%s, offset=%s, payload_size=%s)'% tuple(args)
        
    def __call__(self, game):
        # scan game, ignore spatials
        col_pat = pachi.scan_raw_patterns(game, patargs='xspat=0', skip_empty=False)
        
        buckets = {}
        for color in PLAYER_COLORS:
            buckets[color] = numpy.zeros(len(self.move_preds))
    
        for movenum, (color, pat) in enumerate(col_pat):
            if pat.has_feature('capture'):
                captured = pat.first_payload('capture') >> self.offset
                captured = (2 ** self.payload_size - 1 ) & captured
                
                move_bucket = first_true_pred(self.move_preds, movenum + 1) # counted from zero
                buckets[color][move_bucket] +=  captured
        
        ret = {}
        for color in PLAYER_COLORS:
            ret[color] = numpy.zeros(3 * len(self.move_preds))
        
        for mp in xrange(len(self.move_preds)):
            for color in PLAYER_COLORS:
                # I captured
                ret[color][3 * mp] =  buckets[color][mp]
                # I lost
                ret[color][3 * mp + 1] =  buckets[the_other_color(color)][mp]
                # diff
                ret[color][3 * mp + 2] =  ret[color][3 * mp] - ret[color][3 * mp + 1]
                
    
        return BlackWhite(ret[PLAYER_COLOR_BLACK], ret[PLAYER_COLOR_WHITE])
    
## game -> BlackWhite( vector_black, vector_white )
class BWWinStatVectorGenerator:
    def __init__(self):
        self.annotations = [
                             '(wins by points)',
                             '(wins by resign)',
                             '(wp - wr)', 
                             '(lost by points)', 
                             '(lost by resign)', 
                             '(lp - lr)'
                             ]
        self.types = [ "continuous" ] * len(self.annotations)
        
    def __repr__(self):
        return 'BWWinStatVectorGenerator2()'
        
    def __call__(self, game):
        """"""
        result = str(game.sgf_header.get('RE', '0'))
        
        if result.lower() in ['0',  'jigo',  'draw']:
            raise ProcessingError(repr(self) + " Jigo")
        
        match = re.match(r'^([BW])\+(.*)$', result)
        if not match:
            raise ProcessingError(repr(self) + ' Could not find result sgf tag.')
        
        player, val = match.group(1),  match.group(2)
        if ( val.lower().startswith('f') or  # forfeit
             val.lower().startswith('t') ):  # time
            raise ProcessingError(repr(self) + ' Forfeit, time.')
        
        loses = [0, 0, 0]
        # by resign
        if val.lower().startswith('r'):
            wins = [0, 1, -1]
        else:
            # by points
            try:
                points = float(val)
            except ValueError:
                raise ProcessingError(repr(self) + ' Points not float.')
            wins = [1, 0, 1]
        
        if player == 'B':
            black = numpy.array( wins + loses )
            white = numpy.array( loses + wins )
        else:
            white = numpy.array( wins + loses )
            black = numpy.array( loses + wins )
        
        return BlackWhite(black, white)

    
            
## game -> BlackWhite( vector_black, vector_white )
class BWWinPointsStatVectorGenerator:
    def __init__(self):
        self.annotations = [
                             '(wins #points)',
                             '(loses #points)',
                             ]
        self.types = [ "continuous" ] * len(self.annotations)
        
    def __repr__(self):
        return 'BWWinPointsStatVectorGenerator2()'
        
    def __call__(self, game):
        """"""
        result = str(game.sgf_header.get('RE', '0'))
        
        if result.lower() in ['0',  'jigo',  'draw']:
            raise ProcessingError(repr(self) + " Jigo")
        
        match = re.match(r'^([BW])\+(.*)$', result)
        if not match:
            raise ProcessingError(repr(self) + ' Could not find result sgf tag.')
        
        player, val = match.group(1),  match.group(2)
        if ( val.lower().startswith('f') or  # forfeit
             val.lower().startswith('t') or  # time
             val.lower().startswith('r')     # resign 
             ): 
            raise ProcessingError(repr(self) + ' Forfeit, time, resign.')
        
        try:
            points = float(val)
        except ValueError:
            raise ProcessingError(repr(self) + ' Points not float.')
        
        # if black wins 
        black = numpy.array( [points,  0] )
        white = numpy.array( [0,  points] )
        # if white wins 
        if player == 'W':
            black,  white =  white, black
            
        return BlackWhite(black, white)

#                                 - for black - transform_rawpatfile - 
#                                / 
# game -> raw_patternscan_game --
#                                \ 
#                                 - for white  ----- || -----

#@cache_result
@declare_pure_function
def raw_patternscan_game(game, spatial_dict, patargs=''):
    assert spatial_dict.exists(warn=True)
    ret = utils.get_output_resultpair(suffix='.raw.pat') 

    with open(ret.black.filename, mode='w') as fb:
        with open(ret.white.filename, mode='w') as fw:
            for color, pat in scan_raw_patterns(game, spatial_dict, patargs=patargs):
                fd = fb if color == PLAYER_COLOR_BLACK else fw
                # write output for the desired player
                fd.write("%s\n"%pat)
                #logging.debug(gtp + ":" + pat)

    #logging.info("Generated Raw Patternfiles for game %s, %s"%(game, ret))
    return ret

#@cache_result
@declare_pure_function
def transform_rawpatfile(rawpat_file, ignore=set(), transform={}, ignore_empty=True):
    """Transforms raw pattern file line by line, by ignoring certain features (and their payloads)
    @ignore and transforming payloads with @transform. If @ignore_empty is specified,
    empty patterns are ignored.

    transform_rawpatfile(file, ignore=set('s', 'cont'), transform={'border':lambda x: x - 1})
    (s:20)
    (s:10 border:5 cont:10)
    (s:20 cont:1)
    (capture:18)

    will produce
    (border:4)
    (capture:18)
    """

    ret = get_output_resultfile('.raw.pat')
    with open(ret.filename, mode='w') as fout:
        with open(rawpat_file.filename, mode='r') as fin:
            for line in fin:
                pat = pachi.Pattern(line).reduce(lambda feat, _: not feat in ignore)
                fpairs = []
                for f, p in pat:
                    p = transform.get(f, lambda x:x)(p)
                    fpairs.append((f, p))
    
                if ignore_empty and not fpairs:
                    continue
    
                fout.write( "%s\n"%pachi.Pattern(fpairs=fpairs) )
    return ret

#@cache_result
@declare_pure_function
def summarize_rawpat_file(rawpat_file):
    """Transforms raw pattern file into summarized one:
    (s:20)
    (s:10 border:5)
    (s:20)
    (s:40)
    (s:20)
    ========>
      3 (s:20)
      1 (s:10 border:5)
      1 (s:40)
    """
    result_file = get_output_resultfile('.pat')

    script="cat %s | sort | uniq -c | sort -rn > %s "%(rawpat_file.filename, result_file.filename)

    p = subprocess.Popen(script, shell=True, stderr=PIPE)    
    _, stderr = p.communicate()
    if stderr:
        logging.warn("subprocess summarize stderr:\n%s"%(stderr,))
    if p.returncode:
        raise RuntimeError("Child sumarize failed, exitcode %d."%(p.returncode,))

    return result_file

class SummarizeMerger(models.Merger):
    """Used to sum Summarized Pattern files:
    patfile_1:
      3 (s:20)
      1 (s:10 border:5)
      1 (s:40)

    patfile_2:
      3 (s:20)
      2 (s:15)
      1 (s:10 border:5)

    m = SummarizeMerger()
    m.add(patfile_1)
    m.add(patfile_2)
    patres = m.finish()

    Now, patres is:
      6 (s:20)
      2 (s:15)
      2 (s:10 border:5)
      1 (s:40)
    """
    def __init__(self):
        self.reset()
        
    def start(self, bw_gen):
        self.reset()
    
    def reset(self):
        self.cd = {}

    def add(self, pat_file, color):
        with open(pat_file.filename) as fin:
            for line in fin:
                match = re.match(pat_file_regexp, line)
                if not match:
                    raise IOError("Wrong file format: " + pat_file)
                count, pattern = int(match.group(1)), match.group(2)
                self.cd[pattern] = self.cd.get(pattern, 0) + count

    def finish(self):
        result_file = get_output_resultfile('.pat')
        with open(result_file.filename, 'w') as fout:
            firstlen = None
            for pattern, count in sorted(self.cd.iteritems(), key=lambda kv : - kv[1]):
                if firstlen == None:
                    # get number of decimal places, so that the file is nicely formatted
                    firstlen = 1 + int(math.log10(count))

                # prefix the count with 2 spaces, see pat_file_regexp for format
                s = "%" + str(2 + firstlen) + "d %s\n"
                fout.write(s%(count, pattern))

        self.reset()
        return result_file
    
    
class VectorSumMerger(models.Merger):
    def __init__(self):
        self.reset()
        
    def start(self, bw_gen):
        assert all( tp == 'continuous' for tp in bw_gen.types )
        self.sofar = numpy.zeros(len(bw_gen.types))
        
    def reset(self):
        self.sofar = None
        
    def add(self, vector, color=None):
        if self.sofar == None:
            self.sofar = numpy.zeros(vector.shape)
        self.sofar += vector
        
    def finish(self):
        if self.sofar == None:
            self.sofar = numpy.zeros(0)
        ret = self.sofar
        self.reset()
        return ret
    
class VectorArithmeticMeanMerger(models.Merger):
    def __init__(self):
        self.reset()
        
    def start(self, bw_gen):
        self.reset()
        self.summ.start(bw_gen)
        
    def reset(self):
        self.count = 0
        self.summ = VectorSumMerger()
        
    def add(self, vector, color=None):
        self.count += 1
        self.summ.add(vector)
        
    def finish(self):
        if not self.count:
            ret = self.summ.finish()
        else:
            ret = self.summ.finish() / self.count
            
        self.reset()
        return ret
    
# so that the fc has nice repr
@declare_pure_function
def identity(obj):
    return obj

@declare_pure_function
def linear_rescale(vec, a=-1,  b=1):
    """Linearly rescales elements in vector so that:
        min(vec) gets mapped to a
        max(vec) gets mapped to b
        the intermediate values get remapped linearly between
        """
    assert a <= b
    MIN, MAX = vec.min(), vec.max()
    if MIN == MAX:
        # return average value of the set
        return (float(a + b) / 2) * numpy.ones(vec.shape)
    return a + (vec - MIN) * ( float(b - a) / (MAX -  MIN) )

@declare_pure_function
def natural_rescale(vec):
    return vec / numpy.sum(vec)

@declare_pure_function
def log_rescale(vec, a=-1,  b=1):
    return linear_rescale(numpy.log(1  + vec), a, b)

class VectorApply(models.Merger):
    def __init__(self, merger,
                 add_fc=identity,
                 finish_fc=identity ):
        self.merger =  merger
        self.finish_fc = finish_fc
        self.add_fc = add_fc
        
    def start(self, bw_gen):
        self.merger.start(bw_gen)
        
    def add(self, vector, color=None):
        self.merger.add(self.add_fc(vector), color)
        
    def finish(self):
        return self.finish_fc( self.merger.finish() )
    
    def __repr__(self):
        return "VectorApply(%s, add_fc=%s, finish_fc=%s)" % (repr(self.merger),
                                                             repr(self.add_fc),
                                                             repr(self.finish_fc))
    
class PatternVectorMaker:
    def __init__(self, all_pat, n):
        self.all_pat = all_pat
        self.n = n
        
        self.annotations = []
        self.pat2order = {}
        
        with open(self.all_pat.filename, 'r') as fin:
            # take first n patterns
            for num, line in enumerate(fin):
                if num >= self.n:
                    break
                match = re.match(pat_file_regexp, line)
                if not match:
                    raise IOError("Wrong file format: " + self.all_pat)
                pattern = match.group(2)
                self.pat2order[pattern] = num 
                self.annotations.append(pattern)
        
        self.types = [ "continuous" ] * len(self.annotations)
        
        if len(self.pat2order) < self.n:
            raise ValueError("Input file all_pat '%s' does not have enough lines."%(self.all_pat))
        
    def __repr__(self):
        return "PatternVectorMaker(all_pat=%s, n=%d)"%(self.all_pat, self.n)
    
    def __call__(self, sum_patfile):
        vector = numpy.zeros(self.n)
        added = 0
        with open(sum_patfile.filename, 'r') as fin:
            for line in fin:
                match = re.match(pat_file_regexp, line)
                if not match:
                    raise IOError("Wrong file format: " + str(sum_patfile))
                
                index = self.pat2order.get(match.group(2), None)
                if index != None:
                    vector[index] += int(match.group(1))
                    added += 1
                    
                    # no need to walk through the whole files, the patterns (match.group(2))
                    # are unique since the patfile is summarized
                    if added >= self.n:
                        break
                
        return vector
    
## game -> BlackWhite( vector_black, vector_white )
class BWPatternVectorGenerator:
    def __init__(self, bw_game_summarize, pattern_vector_maker):
        self.pattern_vector_maker = pattern_vector_maker
        self.bw_game_summarize = bw_game_summarize
        
        self.annotations = pattern_vector_maker.annotations
        self.types = pattern_vector_maker.types
    
    def __repr__(self):
        return "BWPatternVectorGenerator(bw_game_summarize=%s, pattern_vector_maker=%s)"%(
                repr(self.bw_game_summarize), repr(self.pattern_vector_maker))
        
    def __call__(self, game):
        bw = self.bw_game_summarize(game)
        return bw.map_both(self.pattern_vector_maker)

#@cache_result
@declare_pure_function
def process_game(game, init, pathway):
    bw = init(game)
    return bw.map_pathway(pathway)

@cache_result
@declare_pure_function
def process_one_side_list(osl, merger, bw_processor):
    return osl.for_one_side_list( merger, bw_processor)

## Process One Side List
class OSLVectorGenerator:
    """
    Maps one side lists to vectors, using different game vector generators (e.g. BWPatternVectorGenerator), e.g:
   OSLVectorGenerator([(vg1, m1), (vg2, m2)]) 
             
game1       m1.add(vg1(game1))      m2.add(vg2(game1))
game2       m1.add(vg1(game2))      m2.add(vg2(game2))
.                   |                       |
.                   |                       |
.                   |                       |
game666     m1.add(vg1(game666))    m2.add(vg2(game666))
            m1.finish()             m2.finish()
               = [1,2,3,4,5]           = [6,7,8,9,10]
            vg1.annotations         vg2.annotations
             = [f1, ..., f5]          =[f6, ..., f10]
    ----------------------------------------------
    result = [  1,2,3,4,5,6,7,8,9,10 ]
    annotations = [ f1, ..., f10 ]
    """
    def __init__(self, gen_n_merge, annotate_featurewise=True):
        self.gen_n_merge = gen_n_merge
        self.annotate_featurewise = annotate_featurewise
        self.functions = []
        self.annotations = []
        self.types = []
        
        for num, (game_vg, merger) in enumerate(gen_n_merge):
            self.functions.append(
                # this function maps one_side_list to a vector
                # where vectors from a game in the osl are merged using the merger
                partial_right(process_one_side_list, merger, game_vg ))
            
            anns = game_vg.annotations
            if annotate_featurewise:
                anns = [ 'f%d%s' % (num, an) for an in anns ]
                
            self.annotations.extend(anns)
            self.types.extend(game_vg.types)
            
    def __repr__(self):
        return "OSLVectorGenerator(gen_n_merge=%s, annotate_featurewise=%s)"%(repr(self.gen_n_merge),
                                                                              repr(self.annotate_featurewise) )
        
    def __call__(self, osl):
        # stack vectors from different generators together
        return numpy.hstack( [ f(osl) for f in self.functions ] )

def make_all_pat(osl, bw_summarize_pathway):
    return process_one_side_list(osl, SummarizeMerger(), bw_summarize_pathway)

@cache_result
@declare_pure_function
def osl_vector_gen_cached(osl_gen, osl):
    """Just to emulate caching for osl_gen.__call__ method.
    this is a bit ugly, since this should really be handled by the caching itself to allow for
    decorating class methods."""
    return osl_gen(osl)

@declare_pure_function
def minus(a,b):
    return a-b

@cache_result
@declare_pure_function
def make_tab_file(datamap, vg_osl, osl_name_as_meta=True, osl_size_as_meta=True, image_name_as_meta=True):
    """As specified in  http://orange.biolab.si/doc/reference/Orange.data.formats/
    If image_name_as_meta or osl_name_as_meta parameters are present, the names of the
    respective objects are added as meta columns.
    """
    tab_file = utils.get_output_resultfile('.tab')
    
    def tab_denoted(fout,  l):
        """Writes tab-denoted elements of list @l to output stream @fout"""
        strings = map(str, l)
        for el in strings:
            if '\t' in el:
                raise RuntimeError("Elements of tab-denoted list must not contain tabs.")
        fout.write('\t'.join(strings) + '\n')
        
    def get_meta(osl_m, osl_size_m, image_m):
        return list( itertools.compress((osl_m, osl_size_m, image_m),
                                        (osl_name_as_meta, osl_size_as_meta, image_name_as_meta)))
    
    with open(tab_file.filename,  'w') as fout:
        # annotations - column names
        tab_denoted(fout, chain( vg_osl.annotations,
                                 datamap.image_annotations,
                                 get_meta('OSL name', 'OSL size', 'Image name')))
        
        # column data types
        tab_denoted(fout, chain( vg_osl.types,
                                 datamap.image_types,
                                 get_meta('string', 'continuous', 'string')))
        
        # column info type: empty (normal columns) / class (main class attribute) / multiclass / meta
        tab_denoted(fout, chain( # attributes are no class
                                 [''] * len(vg_osl.types), 
                                 # for the first class attribute if present
                                 [ 'class' ] * len(datamap.image_types[:1]), 
                                 # for the following class attributes if present
                                 [ 'meta' ] * len(datamap.image_types[1:]), 
                                 #[ 'multiclass' ] * len(datamap.image_types[1:]), 
                                 # meta information if requested
                                 get_meta('meta', 'meta', 'meta')))
        
        # the data itself
        for num, (osl, image) in enumerate(datamap):
            logging.info('Tab file %d%% (%d / %d)'%(100* (num+1) / len(datamap),  num+1,  len(datamap)))
            
            tab_denoted(fout, chain( # the osl
                                     osl_vector_gen_cached(vg_osl, osl), 
                                     # the image
                                     map(float, image.data), 
                                     # the meta data 
                                     get_meta(osl.name, float(len(osl)), image.name)))

    return tab_file

#
##
#
##          Playground:
#
##
#

if __name__ == '__main__':
    def test1():
        ## import'n'init
    
        import logging
        from logging import handlers
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        ch = handlers.WatchedFileHandler('LOG', mode='w')
        logger.addHandler(ch)
    
        from models import Game, GameList, OneSideList, PLAYER_COLOR_BLACK, PLAYER_COLOR_WHITE
        from my_session import my_session_maker
    
        import db_cache
        db_cache.init_cache(filename=None, log=True)
        s = my_session_maker(filename=':memory:')#, echo=True)
    
        ## Prepare data
    
        """
        gl = GameList("pokus")
        s.godb_add_dir_as_gamelist('./files', gl)
        s.add(gl)
    
        osl = OneSideList("all.pat")
        osl.batch_add(gl.games, PLAYER_COLOR_BLACK)
        osl.batch_add(gl.games, PLAYER_COLOR_WHITE)
        s.add(osl)
        s.commit()
        """
        #game = s.godb_sgf_to_game('/home/jm/megaschaf-bronislav.sgf')
    
        ## Prepare the pattern vector game processing pathway
        ## game -> BlackWhite( vector_black, vector_white )
    
        spatial_dict = generate_spatial_dictionary(gl, spatmin=2)
    
        # the pathway: game -> bw rawpat files -> bw transformed rawpat files -> bw summarized pat files 
        bw_game_summarize = partial_right(process_game,
                                          partial_right(raw_patternscan_game, spatial_dict),
                                          [ partial_right(transform_rawpatfile,
                                                          #transform={ 'border':partial_right(minus, 1) },
                                                          ignore=['border', 'cont']),
                                            summarize_rawpat_file
                                            ])
        all_pat = make_all_pat(osl, bw_game_summarize)
        
        vg_pat = BWPatternVectorGenerator( bw_game_summarize,
                                  PatternVectorMaker(all_pat, 100) )
        vg_local = BWLocalSeqVectorGenerator()
        vg_bdist = BWBdistVectorGenerator()
        
        ## Process One game
        
        
        """
        print vg_pat(game)
        print vg_local(game)
        print vg_bdist(game)
        """
        
        ## Process One Side List
        
        gen_n_merge = [ (vg_pat, VectorSumMerger()), 
                        (vg_local, VectorArithmeticMeanMerger()),
                        (vg_bdist, VectorArithmeticMeanMerger())]
       
        vg_osl = OSLVectorGenerator(gen_n_merge)
        
        generate = partial( osl_vector_gen_cached, vg_osl)
        
        # not cached
        #vec, annotations = vg_osl(osl), vg_osl.annotations
        
        # cached
        vec, annotations = generate(osl), vg_osl.annotations
        
        for i in xrange(len(annotations)):
            print vec[i], '\t\t', annotations[i]
        
    
    def test_rescale():
        import numpy
        from pylab import figure,  scatter,  subplot, show
        
        vec =  numpy.random.random( size=10)    
        print vec    
        print linear_rescale(vec, a=-20,  b=20)    
        
        vec = numpy.array([ 452915.,  288357.,  271245.,  111039.,   84811.,   74074.,
             58663.,   62257.,   55296.,   46359.,   51022.,   41049.,
             31297.,   35259.,   34467.,   30918.,   29869.,   36875.,
             29592.,   28075.,   25823.,   27479.,   26343.,   26964.,
             24093.,   24724.,   23135.,   22266.,   21725.,   21769.,
             20130.,   21625.,   20200.,   20619.,   19741.,   19049.,
             17434.,   20167.,   19830.,   16458.,   16513.,   21720.,
             20933.,   20216.,   18414.,   17442.,   12046.,   16186.,
             16732.,   16142.,   15126.,   15332.,   15435.,   12925.,
             14072.,   16321.,   11391.,   14884.,   13147.,   15162.,
             14247.,   15578.,   11826.,   12009.,   11533.,   12349.,
             12219.,   12590.,   10581.,   14550.,   10699.,   12384.,
             11795.,   10769.,   12617.,   12576.,   12281.,   11311.,
             12479.,   11327.,   11398.,   11814.,   11050.,   10248.,
             10506.,   11541.,   12401.,    9580.,   11201.,   10704.,
              9766.,   10402.,    9422.,   12888.,    9473.,    9536.,
             10933.,   10844.,   11005.,    8112.,       0.])
        
        figure(1)
        subplot(321)
        scatter(range(len(vec)), vec,  marker='x',  c='r')
        subplot(322)
        scatter(range(len(vec)), linear_rescale(vec),  marker='x',  c='g')
        subplot(323)
        scatter(range(len(vec)), numpy.log(1 + vec),  marker='x',  c='b')
        subplot(324)
        scatter(range(len(vec)), log_rescale(vec),  marker='x', c='y')
        subplot(325)
        scatter(range(len(vec)), vec / sum(vec),  marker='x',  c='b')
        show()
        
    def test_bdist_hist():
        from my_session import my_session_maker
        s = my_session_maker(filename=':memory:')#, echo=True)
        game = s.godb_sgf_to_game('./files/test_bdist2.sgf')
        
        bdg = BWBdistVectorGenerator(by_line=[2, 3, 4],  by_moves=[4, 6])
        bw =  bdg(game)
        assert len(bdg.annotations) ==  len(bw[0]) ==  len(bw[1])
        
        print "Interval \t\tBlack\tWhite"
        print "-" *  40
        for ann, b, w in zip( bdg.annotations, bw[0], bw[1] ):
            print "%s\t\t"%(ann),  int(b), "\t", int(w)
        
    def test_win_stat():
        from my_session import my_session_maker
        s = my_session_maker(filename=':memory:')#, echo=True)
        #gl =  s.godb_add_dir_as_gamelist('./files/')
        
        game = s.godb_sgf_to_game('../data/go_teaching_ladder/reviews/5443-breakfast-m711-A2.sgf')
        
        print game
        
        bdg = BWWinStatVectorGenerator()
        #bdg = BWWinPointsStatVectorGenerator()
        bw =  bdg(game)
            #continue
        
        assert len(bdg.annotations) ==  len(bw[0]) ==  len(bw[1])
        
        print "Interval \t\tBlack\tWhite"
        print "-" *  40
        for ann, b, w in zip( bdg.annotations, bw[0], bw[1] ):
            print "%30s\t\t" % (ann),  b, "\t", w
        
    ##
    ##
    
    test_bdist_hist()
    #test_capture_hist()
    #test_win_stat()
