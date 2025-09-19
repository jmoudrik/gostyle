import re
import os
import logging
from godb import rank

RECO_DIR = 'RECO'
AFFIL_KEY = "?acc=aab3238922bcc25a6f606eb525ffdc56"
MAX_RECO = 4
#rank.Rank.from_string("h")

class RecoInt:
    def __init__(self, l):
        self.l = l
        self.name = l[0]
        self.link = l[3]
        self.lo = rank.Rank.from_string(l[1]).key()
        self.hi = rank.Rank.from_string(l[2]).key()
        assert self.lo <= self.hi
        self.s = self.hi - self.lo
        self.m = (self.hi + self.lo) / 2
        
    def similarity(self, val):
        return max( float(self.s - abs(self.m - val)) /  self.s,  0.0)
    
    def to_link(self):
        return '<a href="%s">%s</a>' % (self.link + AFFIL_KEY, self.name)
    
    def direction_modifier(self, strength):
        sim = self.similarity(strength)
        if sim < 0.4:
            return ''
        return 'slightly '
        
    def direction(self, strength):
        if strength > self.m:
            return 'harder'
        return 'easier'
    
    def direction_string(self, strength):
        sim = self.similarity(strength)
        if sim < 0.7:
            return " (%s%s)" % (self.direction_modifier(strength),
                                self.direction(strength))
        return ''
    
    def __repr__(self):
        return str(self.l)
    
    def __str__(self):
        return str(self.l)

def read_file(filename):
    ret = []
    stack = []
    with open(filename, 'r') as fin:
        for line in fin:
            assert isinstance(line, str)
            
            if re.match("[ ]*#", line) or re.match("^\s*$", line):
                continue
            
            stack.append(line.rstrip())
            
            if len(stack) == 4:
                ret.append(RecoInt(stack))
                stack = []
    return ret
                
def find_best(l, val):
    dl = map(lambda ri: (ri.similarity(val), ri), l)
    dl.sort(reverse=True)
    
    dl = filter(lambda (sim, ri): sim, dl)
    
    #for sim,  ri in dl:
        #print sim,  ri.name
        
    return dl

def generate_recommendations(str_val):
    HE_o = "<h4>"
    HE_c = "</h4>"
    
    def suit2perc(suit):
        return "%.0f%%" % (100.0 * ( suit + 0.2) / 1.2)
        return "%.0f%%" % (100.0 * suit )
        return "%.0f%%" % (100.0 * ( suit + 1.0) / 2)
    
    to_say = []
    keys = [ 'by_level', 'by_series', 'by_book']
    d = {}
    for key in keys:
        d[key] = find_best(read_file(os.path.join(RECO_DIR, key)), str_val)
        #print
        #print key, d[key]
        
    first = d['by_level'][0]
    
    if first[0] > 0.7 or len(d['by_level']) == 1: 
        to_say.append( """<p>Generally speaking, we recommend %s books.
More detailed tips follow.</p>"""%(first[1].to_link()) )
        
    else:
        if first[0] < 0.5:
            logging.warn(
"""Weird ordering of books by level, probably strength='%s' out of bound??
d = %s"""%(str_val, repr(d)))
            
        sec = d['by_level'][1]
        to_say.append( """
<p>Generally speaking, we recommend either %s books of %s level
or %s books of %s level. More detailed tips follow.</p>
        """%(# the direction gives position of the interval with respect to player
             #    "interval is hard for player"
             # we want negation because we want to say
             #     "choose easier books from the harder interval"
             # or
             #     "choose harder books from the easier interval"
             
             sec[1].direction(str_val),  first[1].to_link(),  
             first[1].direction(str_val), sec[1].to_link(), ))
        
        
    for key in ['by_series', 'by_book']:
        if d[key]:
            if key == 'by_series':
                to_say.extend([ HE_o + "Series" + HE_c,
                """<p>We find the following <b>series</b> of books to be suitable: <ul>""" ])
            if key == 'by_book':
                to_say.extend([ HE_o + "Books" + HE_c,
                """<p>Apart from the series, we recommend the following single <b>books</b>: <ul>""" ])
                
            for score, ri in d[key][:MAX_RECO]:
                to_say.append("<li>%s%s &#8212; %s</li>"%(suit2perc(score),
                                                          ri.direction_string(str_val),
                                                          ri.to_link()) )
                
            to_say.append("</ul></p>")
        
    return '\n'.join(to_say)
        
        
if __name__ == "__main__":
    
    test_style = {
	 'te' : { 'val': 1, 'sigma' : 1.2, 'pic': 'out2.png'},
	 'or' : { 'val': 1, 'sigma' : 1.2, 'pic': 'out2.png'},
	 'ag' : { 'val': 1, 'sigma' : 1.2, 'pic': 'out2.png'},
	 'th' : { 'val': 1, 'sigma' : 1.2, 'pic': 'out2.png'},
         }
    test_str = { 'val': 1, 'sigma' : 1.2, 'pic': 'out2.png'}
    
    
    print generate_reco(8)
    
        
    