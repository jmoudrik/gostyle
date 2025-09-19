import re
import subprocess
import os
import copy
from os.path import abspath, exists
import shutil
import functools
import inspect
import itertools

from config import OUTPUT_DIR
import misc
from colors import BlackWhite
import types

VIEWER_LIST=['qgo', 'kombilo']

def viewer_open(sgf_filename, executable=VIEWER_LIST[1]):
    p = subprocess.Popen([executable, sgf_filename])
    return

def bark():
    subprocess.call('bark', shell=True)

def check_output(*args,  **kwargs):
    if hasattr(subprocess, 'check_output'):
        return subprocess.check_output(*args, **kwargs)
    else:
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *args, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = args[0]
            raise subprocess.CalledProcessError(retcode, cmd, output=output)
        return output

def get_year(datestr,  match_century=True):
    """Function trying to extract date from a string - usually a DT field of a sgf_file.
    First, look for the first year string in the @datestr.
    if not found and the @match_century is true, we look for strings like
    "18th century", which results in year 1750 (the mean of years in 18th century)
    
    Returns None if no year found.
    """
    # 1982-10-10
    # note the non-greedy .*? expansion => the first date string in the result gets matched
    # that is get_year("1982 1999") = 1982
    match = re.match( '.*?([0-9]{4}).*', datestr)
    if match:
            return int(match.group(1))
        
    if match_century:
        # 17th century, 18th c.
        match = re.match( '.*[^0-9]?([0-9]{2}th c).*', datestr)
        if match:
            century = int(match.group(1)[:2])
            # returns "mean" year of the century:
            # 17th century -> 1650
            return century * 100 - 50
    
    return None

class ResultFile:
    def __init__(self, filename, create_empty=False):
        self.filename = filename
        if create_empty:
            assert not self.exists()
            open(self.filename,'w').close()
            
    def exists(self, warn=False):
        status = exists(self.filename)
        if not status and warn:
            logging.warn("File '%s' does not exist."%(self.filename,))
        return status
            
    def __repr__(self):
        return "ResultFile('%s')"%(self.filename,)

def get_random_output_base(sub_len=3, levels=1):
    h = misc.unique_hash()
    assert len(h) > levels * sub_len
    assert levels >= 1
    l = [OUTPUT_DIR]
    for x in xrange(levels):
        l.append( h[ x * sub_len : (x+1) * sub_len ] )
        
    d = os.path.join(*l)
    if not os.path.isdir(d):
        os.makedirs(d)
    return os.path.join(d, h)
    
def get_output_resultfile(suffix=''):
    
    ret = ResultFile( get_random_output_base() + suffix)
    if ret.exists():
        raise RuntimeError("New output result file '%s' already exists, unique hash not really unique..."%(ret))
    return ret

def get_output_resultpair(suffix=''):
    basename = get_random_output_base()
    ret1 = ResultFile(basename + '_B' + suffix)
    ret2 = ResultFile(basename + '_W' + suffix)
    rettup = BlackWhite(ret1, ret2)
    for ret in rettup:
        if ret.exists():
            raise RuntimeError("New output result file '%s' already exists, unique hash not really unique..."%(ret))
    return rettup

def get_poly_s(coefs):
    """Returns a string with polynomial equation; e.g.:
    
    >>> from utils import get_poly_s
    >>> get_poly_s([0.5,0,4])
    'y = 0.50x^2 + 4.00'
    >>> get_poly_s([1,2,3,4])
    'y = 1.00x^3 + 2.00x^2 + 3.00x + 4.00'
    """
    C = []
    for pw, co in enumerate(reversed(coefs)):
        if co:
            s = "%.2f" % co
            if pw:
                s += 'x'
                if pw > 1:
                    s += '^%d' % pw
            C.append(s)
    return 'y = ' + ' + '.join(reversed(C))

def first_true_pred(predicates, value):
    """Given a list of predicates and a value, return the index of first predicate,
    s.t. predicate(value) == True. If no such predicate found, raises IndexError."""
    for num, pred in enumerate(predicates):
        if pred(value):
            return num
    raise IndexError

class MyPartial:
    def __init__(self, func, args=(), keywords={}, right=False):
        self.func = func
        self.args = args
        self.keywords = keywords
        self.right = right
        
    def _frepr(self):
        if isinstance(self.func, MyPartial):
            return repr(self.func)
        
        return repr(self.func)
        
    def __repr__(self):
        return "MyPartial(%s, %s, %s%s)"%(self._frepr(),
                                          repr(self.args), repr(self.keywords),
                                          ", right=True" if self.right else '')
    
    def _merge_args(self, args_new):
        if self.right:
            return args_new + tuple(self.args)
        return tuple(self.args) + args_new
    
    def _merge_kwargs(self, kwargs_new):
        kwargs = self.keywords.copy()
        kwargs.update(kwargs_new)
        return kwargs
    
    def __call__(self, *args_new, **kwargs_new):
        args = self._merge_args(args_new)
        kwargs = self._merge_kwargs(kwargs_new)
        return self.func(*args, **kwargs)
    
def partial(f, *args, **kwargs):
    """
    def minus(a, b):
        return a - b
    
    partial(minus, 10)  is like:
    
    lambda b : minus(10, b)
    """
    return MyPartial(f, args, kwargs)

def partial_right(f, *args, **kwargs):
    """
    def minus(a, b):
        return a - b
    
    partial_right(minus, 10)  is like:
    
    lambda a : minus(a, 10)
    """
    return MyPartial(f, args, kwargs, right=True)


class ReprWrapper(object):
    def __init__(self, repr_f, f):
        self.repr_f = repr_f
        self.f = f
        functools.update_wrapper(self, f)
    def __call__(self, *args, **kwargs):
        return self.f(*args, **kwargs)
    def __repr__(self):
        return self.repr_f(self.f)
    
def repr_origin(f):
    if hasattr(f, 'im_class'):
        prefix = f.im_class
    else:
        prefix = f.__module__
    return "%s.%s"%(prefix, f.__name__)

def head(f, n=10):
    print f.filename
    with open(f.filename, 'r') as fin:
        for line in itertools.islice(fin, n):
            print line

def iter_splits(l, parts=None, max_size=None, min_size=None):
    """Will yield consequent sublist of the @l list, trying to result
    evenly sized sublists.  Exactly one of the parameters @parts or
    @max_size or @min_size must be specified.

    specifiing parts = N will yield N sublists of (almost) even size. The
    list size difference is guaranted to be at most 1.

    >>> list(iter_splits(range(5), parts=2))
    [[0, 1, 2], [3, 4]]
    >>> list(iter_splits(range(5), parts=4))
    [[0, 1], [2], [3], [4]]
    
    
    
    specifiing max_size = N returns the smallest possible number of
    consequent sublists so that whole list is divided and size of each
    part is <= N
    
    >>> list(iter_splits(range(5), max_size=3))
    [[0, 1, 2], [3, 4]]
    >>> list(iter_splits(range(5), max_size=10))
    [[0, 1, 2, 3, 4]]

    Calling iter_splits(l, max_size=N) is just a shorthand for calling
    iter_splits(l, parts=len(l) / N + bool(len(l)% N) )
    
    
    
    Similarly min_size = N returns the largest possible number of
    consequent sublists so that whole list is divided and size of each
    part is >= N
    
    Calling iter_splits(l, min_size=N) is just a shorthand for calling
    iter_splits(l, parts=len(l) / N )
    """
    if bool(parts) + bool(max_size) + bool( min_size) != 1:
        raise TypeError('Exactly one of parts, max_size or exact_size arguments must be specified (and nonzero)')
    
    if parts:
        print parts
        pn, rest = len(l) / parts, len(l) % parts
        if pn == 0:
            raise ValueError("Number of parts to split must not be larger than the number of elements.")
        
        def sizes(pn, rest):
            for i in xrange(parts):
                if rest:
                    yield pn + 1
                    rest -= 1
                else:
                    yield pn
        
        stop = 0
        for size in sizes(pn, rest):
            start, stop = stop, stop + size
            yield l[start: stop]
            
    if max_size:
        pn, rest = len(l) / max_size, len(l) % max_size
        if rest:
            pn += 1
        for split in iter_splits(l, parts=pn):
            yield split
            
    if min_size:
        for split in iter_splits(l, parts=len(l)/min_size):
            yield split
        
def iter_exact_splits(l, split_size):
    tail = copy.copy(l)
    
    while tail:
        head, tail = tail[:split_size], tail[split_size:]
        # the last head could be shorter
        if len(head) == split_size:
            yield head
    
            
if __name__ == '__main__':
    def test_partial():
        def fc ( a, b, c='def C', d='def D' ):
            return "a=%d, b=%d, c=%s, d=%s"%(a,b,c,d)
        
        nor = partial(fc, 20, c=10)
        zpr = partial_right(fc, 20, c=10)
        
        print "puvodni:", repr(fc)
        print "normalni:", repr(nor) 
        print "zprava:", repr(zpr) 
        
        print "normalni(10) = ", nor(10)
        print "zprava(10) = ", zpr(10)
            
        nor2 = partial(nor, 10)    
        print "double:", nor2
        print "double()", nor2()
        
        class Fobj:
            def __call__(self, a, b):
                return "a=%s b=%s"%(a,b)
        
        ca = partial(Fobj(), 10)
        print ca
    
    def test_split():
        l = range(20)
        
        for kw in ['parts', 'max_size',  'min_size']:
            for val in  range(10, 20):
                print "iter_splits(%s, **{%s : %s}))" % (l,  kw,  val)
                res = list(iter_splits(l, **{kw : val}))
                print kw, "=", val
                print "   len = ", len(res), ", max(size) = ", max(map(len, res)), ", min(size) = ", min(map(len, res))
                print "   ", res
                
                assert list(itertools.chain.from_iterable(res)) == l
                if kw == 'parts':
                    assert len(res) == val
                if kw == 'max_size':
                    assert max(map(len, res)) <= val
                if kw == 'min_size':
                    assert min(map(len, res)) >= val
                
    #test_partial()
    #test_split()    
    
    get_random_output_base(0, 1)
