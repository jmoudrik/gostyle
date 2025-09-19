#coding: utf-8
import hashlib
import random
import threading
import os
import time


import urlparse
import urllib
import re
import json
import web
import logging 

from functools import wraps

import config

#
# func
#

def filter_null(it):
   return list( a for a in it if a ) 

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

def get_random_fn():
    return os.path.join(config.OUTPUT_DIR,  unique_hash())


#
# Webpy utils
#

def log_exceptions(f):
    @wraps(f)
    def g(*args,**kwargs):
        try:
            return f(*args, **kwargs)
        except (web.SeeOther, web.Redirect):
            raise
        except Exception as e:
            logging.exception("EXCEPTION: \n"+str(e))
    return g

def provide_callback(f):
    @wraps(f)
    def g(*args,**kwargs):
        data = f(*args, **kwargs)
        
        callback = parseq(web.ctx.query, {"callback" : (None, str)})['callback']
        if callback:
            return "%s(%s);" % (callback,  data)
        return data
    return g

# Query parsing with a default value
# e.g /?id=10&blabol=17

def parseq(q, pd):
    q = re.sub(r'^\?', r'', q)
    d = urlparse.parse_qs(q)
    ret = {}
    for key, l in d.items():
        if not l:
            continue
        if key in pd:
            default, convert_f = pd[key]
            try:
                val = convert_f(l[0])
            except ValueError:
                raise ValueError("Error casting to '%s'."%(str(convert_f)))
            ret[key] = val

    for key, (default, convert_f) in pd.items():
        if not key in ret:
            ret[key] = default

    return ret
