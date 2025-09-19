#coding: utf-8
import unicodedata
from itertools import chain, izip,  count
import hashlib
import random
import logging
import threading
import os
import time
import datetime

def identity(x):
    return x

def filter_null(iterable):
    return [ x for x in iterable if x ]

def filter_both(predicate, iterable):
    yes, no = [], []
    for i in iterable:
        if predicate(i):
            yes.append(i)
        else:
            no.append(i)
    return yes, no

def flatten(list_of_lists):
    return chain.from_iterable(list_of_lists)

def flatten_twice(list_of_lists_of_lists):
    return flatten(flatten( list_of_lists_of_lists ))

def bucket_by_key(iterable, key_fc):
    """
    Throws items in @iterable into buckets given by @key_fc function.
    e.g.
    >>> bucket_by_key([1,2,-3,4,5,6,-7,8,-9], lambda num: 'neg' if num < 0 else 'nonneg')
    {'neg': [-3, -7, -9], 'nonneg': [1, 2, 4, 5, 6, 8]}
    """
    buckets = {}
    for item in iterable:
        buckets.setdefault(key_fc(item), []).append(item)
    return buckets


# given an iterable of pairs return the key corresponding to the greatest value
def argmax(pairs):
    return max(pairs, key=lambda x:x[1])[0]
def argmin(pairs):
    return min(pairs, key=lambda x:x[1])[0]

# given an iterable of values return the index of the greatest value
def argmax_index(values):
    return argmax(izip(count(), values))
def argmin_index(values):
    return argmin(izip(count(), values))

#
# Type info and conversion
#

def is_conv(x, cls):
    try:
        cls(x)
        return True
    except:
        return False

def is_int(x):
    return is_conv(x, int)

def is_float(x):
    return is_conv(x, float)

def is_type_int(x):
    return is_type(x, int)

def is_type_float(x):
    return is_type(x, float)

def is_type(x, type):
    try:
        return x == type(x)
    except:
        return False

#
# Hash utils & random strings
#

def sha256(txt):
    return hashlib.sha256(txt).hexdigest()
def sha512(txt):
    return hashlib.sha512(txt).hexdigest()

def random_hash(LEN=10):
    return str(random.randint(10**(LEN-1),10**LEN-1))

def unique_hash(length=32):
    """Returns "unique" hash. (the shorter the length, the less unique it is).
    I consider one in 16**32 to be pretty unique. :-) (supposing that sha256 works).
    
    (Am I mistaken??)"""
    return sha256( "%.20f %s %d %d"%(time.time(), random_hash(), os.getpid(), threading.current_thread().ident ) ) [:length]

def time_based_random_hash(length=32):
    return unique_hash(length)

def tmp_names(base=random_hash(), first_simple=False):
    i = 0
    if first_simple:
        yield "%s"%(base)
        i += 1
    while True:
        yield "%s_%d"%(base, i)
        i+=1

#
# Text stuff
#

def encode_utf8(st):
    return unicode(st).encode('utf-8')

def remove_accents(istr):
    nkfd_form = unicodedata.normalize('NFKD', unicode(istr))
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])

def unicode2ascii(unistr):
    return remove_accents(unistr).encode('ascii', 'ignore')

def pad2len(s, l, padchar):
    if len(s) < l:
        return s + padchar * (l - len(s)) 
    return s

#
#
#

def iter_files(directory):
    for (dirpath, _, filenames) in os.walk(directory):
        for name in filenames:
                yield os.path.join(dirpath, name)

def timeit(f, *args, **kwargs):
    t0 = time.time()
    ret = f(*args, **kwargs)
    diff = time.time() - t0
    print "TOOK: %.3f sec"%(diff,)
    return ret