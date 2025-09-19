#!/usr/bin/python
import os

import numpy
import pylab
import logging
from collections import namedtuple

import Orange

from game_to_vec import linear_rescale
from utils import get_poly_s



BestMatching = namedtuple('BestMatching', 'attribute poly sqres X Y pearson Xo Yo')

def pearson_coef(vec1, vec2):
    assert vec1.shape == vec2.shape
    def norm(vec):
        return numpy.sqrt((vec*vec).sum())
    def center(vec):
        return vec - vec.mean()
    vec1, vec2 = center(vec1), center(vec2)
    return (vec1 * vec2).sum() / (norm(vec1) * norm(vec2)) 

def best_matching_attributes(table, degree=1,  class_attr=None):
    if class_attr ==  None:
        class_attr =  table.domain.class_var
    print class_attr
    l = []

    # the X coordinates are always the same
    X_orig = numpy.array([ vec[class_attr] for vec in table ], dtype='float')
    # map it to <-1,1>
    X = linear_rescale(X_orig)
    
    for attr in table.domain.attributes:
        # the Y coordinates
        Y_orig = numpy.array([ vec[attr] for vec in table ], dtype='float')
        Y = linear_rescale(Y_orig)

        # take solution and sums of residues
        X, Y = X_orig, Y_orig
        sol, res, r1, r2, r3 = numpy.polyfit(X, Y, degree, full=True)
        l.append(BestMatching(attr, sol, res,
                              X, Y,
                              pearson_coef(X, Y),
                              X_orig, Y_orig
                              ))
    return l


def print_best_scoring(scoring, top=10):
    for m in scoring[:top]:
        print "%5.3f %s" % (m[1], m[0])
    

import subprocess
from config import PACHI_DIR
import re

def get_extra(s, tex=False):
    # if the pattern is spatial, print it
    match = re.search('[\( ]s:([0-9]*)[\) ]', s)
    if match:
        prog = 'pattern_spatial_show.pl' if not tex else 'pattern_spatial_gentex.py'
        script="""
cd %s
./tools/%s %s | sed '/^[[:space:]]*$/d;1s/ .*$//' """%( PACHI_DIR, prog, match.group(1))
        ret = subprocess.check_output(script,  shell=True)
        return ret
        
def mixed_score(bm):
   return bm.sqres / abs(bm.poly[0])

def print_matching(bms, head=None, X_label='', Y_label='Frequency'):
    print "!!! make sure you have proper patterns.spat in", PACHI_DIR
    if head == None:
        head = len(bms)
    #l = sorted(bms, key=lambda bm: -abs(pearson_coef(bm.X, bm.Y)))
    #l = sorted(bms, key=lambda bm: bm.sqres)
    #l = sorted(bms, key=mixed_score )
    l = sorted(bms, key=lambda bm: - abs(bm.pearson))
    
    d = {}
    
    for bm in l[:head]:
        poly =  numpy.poly1d(bm.poly)
        print "%s\n\tpearson:%.3f\n\t-5:%.2f\n\t20:%.2f\n\tpattern: '%s'\n\tpoly: %s" % (
                                                      get_poly_s(bm.poly),
                                                      bm.pearson, 
                                                      numpy.polyval(bm.poly, -5),
                                                      numpy.polyval(bm.poly, 20),
                                                      #mixed_score(bm),
                                                      #bm.sqres,
                                                      bm.attribute.name,
                                                      bm.poly)
        d[str(bm.attribute.name)] = list(bm.poly)
        print get_extra(bm.attribute.name, tex=False)
        gt = get_extra(bm.attribute.name, tex=True)
        gt = None
        if gt:
            with open(os.path.join('OUT_PATT', str(bm.attribute.name) + '.tex'), 'w') as fout:
                fout.write("""
\\documentclass{article}
\\usepackage[paperwidth=10cm, paperheight=10cm]{geometry}
\\usepackage{psgo}
\\pagenumbering{gobble}
\\begin{document}
%s
\\end{document}
"""%gt)

        #print "%s\tpearson_r: %f\tsq-err: %.2f\tpattern: '%s'" % (get_poly_s(bm.poly), pearson_r, bm.sqres, bm.attribute.name)

        #if True:
        if False:
            pylab.xlim(min(bm.X)-0.1, max(bm.X)+0.1)
            pylab.ylim(min(bm.Y)-0.1, max(bm.Y)+0.1)
            # data
            pylab.plot(bm.X, bm.Y, 'x', c='b')
            pylab.xlabel(X_label)
            pylab.ylabel(Y_label)
            # the fitted polynomial
            pylab.plot(bm.X, poly(bm.X),  c='r')
            pylab.title(bm.attribute.name)
            pylab.show()
    print d
        
            
def reduce_table(bms, table, size ):
    l = sorted(bms, key=lambda bm: - abs(bm.pearson))
    
    positive = [ bm.attribute for bm in l if bm.pearson > 0 ]
    negative = [ bm.attribute for bm in l if bm.pearson < 0 ]
    
    newd = Orange.data.Domain( positive[:size] + negative [:size] +
                               [table.domain.class_var] )
    return Orange.data.Table(newd, table)
    
            
def cp_spatials(filename):
    import shutil
    shutil.copy(filename,  PACHI_DIR )

if __name__ ==  "__main__":
    logging.getLogger().setLevel(logging.INFO)
    import sys
    
    def test_style_data():
        def linearly_dependent_patterns(data):
            cls = None
            cls = data.domain.get_metas()[-5]
            bms = best_matching_attributes(data, class_attr=cls)
            bms = filter(lambda bm: abs(bm.pearson) > 0.2, bms )
            #bms = filter(lambda bm: bm.pearson < - 0.2, bms )
            # bms = filter(lambda bm: abs(bm.poly[0]) > 0.1, bms )
            print_matching(bms, X_label=cls)
            
        def quadratic_dependent_patterns(data):
            cls = data.domain.get_metas()[-3]
            #cls = None
            
            bms = best_matching_attributes(data, class_attr=cls, degree=2)
            bms = filter(lambda bm:    # take only non-"flat" guys
                                    abs(bm.poly[0]) > 0.2 and
                                        # quadratic term dominates the linear
                                    abs(bm.poly[0]) >= abs(bm.poly[1])
                                        , bms )
            print_matching(bms, X_label=cls)
        
        basedir = 'TABS/style2_16_12_final_best_all'
        data = Orange.data.Table(os.path.join(basedir,"results.tab"))
        print '\n'.join(map(str, data.domain.get_metas().items()))
        return
        cp_spatials(os.path.join(basedir, "patterns.spat"))
        linearly_dependent_patterns(data)
        #quadratic_dependent_patterns(data)
        
    test_style_data()
    sys.exit()
    
    def test_str_data(filename):
        def linearly_dependent_patterns(data):
            logging.info('Linear analysis, "%s"'%repr(data))
            bms = best_matching_attributes(data)
            # only take such patterns that have sufficiently steep fit
            #  that is, that correlate strongly with the strength
            
            #return filter(lambda bm: abs(bm.poly[0]) > 0.06, bms )
            
            #return filter(lambda bm: bm.pearson > 0.3, bms )
            return filter(lambda bm: abs(bm.pearson) > 0.35, bms )
            
        def quadratic_dependent_patterns(data):
            bms = best_matching_attributes(data, degree=2)
            # not interested in patterns where quadratic term is "used"
            # only to minimize the error. we want patterns with relatively
            # "clear" quadratic dependence
            #  - such as the patterns that are played nor by begginers,
            #  neither good players, but
            #    by middle-level players (bm.poly[0] < 0)
            #  - or patterns that are played by both pros and the
            #  begginers, but disregarded by
            #    the middle players - opposite of previous, "U" like
            #    distribution shape, bm.poly[0] > 0
            #  - we want to discard patterns where the quadratic
            #  coefficient merely makes a "better" linear function
            
            return filter(lambda bm:    # take only non-"flat" guys
                                    abs(bm.poly[0]) > 0.05 and
                                        # quadratic term dominates the linear
                                    abs(bm.poly[0]) >= 2* abs(bm.poly[1])
                                        , bms )
        
        data = Orange.data.Table(filename)
        bms = linearly_dependent_patterns(data)
        #return bms
        #bms = quadratic_dependent_patterns(data)
        
        print_matching(bms,  X_label='Strength')        
        
        #return reduce_table(bms, data, 10)
        
    
    #if len(sys.argv) > 1:
        #fn = sys.argv[1]
        
    #fn =  "./TABS/GTL_10_10_all_pat_800/GTL_10_10_all_pat_800.tab"#./str_data_cropped.tab"
    #def orange_score(data):
        #ma = Orange.feature.scoring.score_all(data)
        #print_best_scoring(ma)
    
    #basedir =  "TABS/KGS_wide_by_player_10_100_120_simple/"
    basedir = 'TABS/KGS_wide_final_best/'
    basedir = 'TABS/KGS_wide_final_fast/'
    cp_spatials(os.path.join(basedir, "patterns.spat"))
    fn =  os.path.join(basedir, 'results.tab')
    data = Orange.data.Table(fn)
    
    #orange_score(data)
    test_str_data(fn)
    #t2.write(filename + '.reduced_10.tab')
    
    #sys.exit()
    
    def test_year_data():
        def linearly_dependent_patterns(data):
            bms = best_matching_attributes(data)
            # only take such patterns that have sufficiently steep fit
            #  that is, that correlate strongly with the strength
            return filter(lambda bm: abs(bm.poly[0]) > 0.01, bms )
        
        data = Orange.data.Table("./TABS/year_data_20_500/year_data_20_500.tab")
        bms = linearly_dependent_patterns(data)
        
        print_matching(bms,  X_label='Year')        
    
    #test_year_data()