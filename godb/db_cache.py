from sqlalchemy import Table, Column, Integer, ForeignKey, Text, Date, PickleType, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import time
import logging
import inspect
import types
import functools

import utils

##
## zmena kodu (a zmena def kwargs) funkce zneplatnuje hodnoty v cachi
##
## hodnoty def kwargs to ovsem meni, jen kdyz se fce predava parametrem (funkci kterou taky cachujeme),
## nikoliv kdyz je volana primo
## pze kdyz se predava parametrem, tak ta vnejsi fce nevi jaky ma def param

Base = declarative_base()
    
# By default (without running init_cache ) a dict (=> cache not persistent across runs & processes)
cache_object = {}
cache_do_logging = False

class CacheLine(Base):
    """
    Maps key -> value, saving time of creation, which is used as a criterion for time expiration.
    """
    __tablename__ = 'cacheline'
    id = Column(Integer, primary_key=True)
    
    time = Column(Float)
    
    key = Column(Text, index=True)
    value = Column(PickleType)
    
    
    def __str__(self):
        return "(%s, %s) -> %s" % (self.key, self.time, self.value)
    
    def __repr__(self):
        return "CacheLine(%s)" % (str(self))
        
        
    
class DBCacheObject:
    """ The cache uses the same interface as dict."""
    def __init__(self, db_session, expire):
        self.session = db_session
        self.expire = expire
    
    def delete_expired(self):
        expired_before = time.time() - self.expire
        self.session.query(CacheLine).filter(CacheLine.time < expired_before).delete()
        self.session.commit()
    
    def __getitem__(self, key):
        # with correct key
        q = self.session.query(CacheLine).filter(CacheLine.key == key)
        
        # if expiration rate set
        if self.expire:
            expired_before = time.time() - self.expire
            # not expired
            q = q.filter(CacheLine.time > expired_before)
            
        # order by time
        by_time = q.order_by(CacheLine.time).all()
        
        # the last one
        if len(by_time):
            return by_time[-1].value
        
        raise KeyError
    
    def __setitem__(self, key, value):
        l = CacheLine(time=time.time(), key=key, value=value)
        self.session.add(l)
        self.session.commit()
        
        
def delete_expired():
    global cache_object
    if not isinstance(cache_object, DBCacheObject):
        logging.warn("Cannot remove expired elemets from cache - not a DBCacheObject")
        return

    logging.info("Deleting expired cache rows...")
    cache_object.delete_expired()
    
def _print_all():
    global cache_object
    
    if isinstance(cache_object, DBCacheObject):
        it = cache_object.session.query(CacheLine).all()
    else:
        it = cache_object.iteritems()
    
    print "CACHE:"
    for a in it:
        print "\t", a
        
        
#
# Pure function 
#

class PureFunction(object):
    """PureFunction is a class that has nice function repr like
    <pure_function __main__.f> instead of the default repr
    <function f at 0x11e5320>.

    By using it, the user declares, that calls to the same function with
    same arguments will always (in time, accross different processes, ..)
    have the same results and can be thus cached.
    """
    def __init__(self, f):
        self.f = f
        assert isinstance(f, types.FunctionType)
        functools.update_wrapper(self, f)
        
    def getargspec(self):
        return inspect.getargspec(self.f)
    
    def get_default_kwargs(self):
        args, varargs, varkw, defaults = self.getargspec()
        if defaults:
            return dict(zip(args[-len(defaults):], defaults))
    
    def __call__(self, *args, **kwargs):
        logging.debug("calling %s"%repr(self))
        return self.f(*args, **kwargs)
    
    def __repr__(self):
        return '<pure_function %s>'%(utils.repr_origin(self.f))
        #return '<pure_function %s def_kwargs=%s>'%(utils.repr_origin(self.f), repr( self.get_default_kwargs()))

# to be used as a deco
declare_pure_function = PureFunction

#
#
#
    
def init_cache(filename='CACHE.db', expires=0, log=False, echo=False):
    """
    Initialize cache, sets up the global cache_object.
    @filename specifies the sqlite dbfile to store the results to, @expires
    specifies expiration in seconds. If you set @expires to 0, cached data is
    valid forever. Setting @cache_log to True logs some DEBUG level information.
    Setting @echo to True outputs sqlalchemy logs as well.
    """
    global cache_object, cache_do_logging
    cache_do_logging = log
    
    if filename == None:
        # By default, the cache object is a dict
        
        if expires and log:
            logging.warn('Dictionary cache object does not support time expiration of cached values!')
        pass
    else:
        engine = create_engine('sqlite:///%s'%filename, echo=echo)
        Base.metadata.create_all(engine) 
        Session = sessionmaker(bind=engine) 
        session = Session()
        
        cache_object = DBCacheObject(session, expires)
    

def close_cache():
    global cache_object
    cache_object.session.close()
    

def make_key(f, f_args, f_kwargs):
    if isinstance(f, PureFunction):
        spect = f.getargspec()
    elif isinstance(f, types.FunctionType):
        spect = inspect.getargspec(f)
    else:
        raise TypeError("Unable to obtain arg specification for function : '%s'"%(repr(f)))
    
    args, varargs, varkw, defaults = spect
    default_kwargs = {}
    if defaults:
        default_kwargs = dict(zip(args[-len(defaults):], defaults))
    for (key, val) in f_kwargs.iteritems():
        assert key in default_kwargs
        
    f_kwargs_joined = default_kwargs
    f_kwargs_joined.update(f_kwargs)
    
    #rep = "%s(args=%s, kwargs=%s)"%(utils.function_nice_repr(f), repr(f_args), repr(f_kwargs_joined))
    
    rep = "%s(%s)"%(repr(f),
                    ', '.join(map(repr, f_args)
                              + [ '%s=%s'%(key, repr( val)) for key, val in f_kwargs_joined.iteritems() ]))
    
    if 'at 0x' in rep:
        logging.warn("Object(s) specified in '%s' do not have a proper repr."%(rep))
            
    return rep
    
#
# The deco
#

def cache_result(fun):
    """Compute the key, look if the result of a computation is in the
    cache. If so, return it, otw run the function, cache the result and
    return it."""
    def g_factory(f):
        def g(*args, **kwargs):
            global cache_object, cache_do_logging
            key = make_key(f, args, kwargs)
            try:
                cached = cache_object[key]
                if cache_do_logging:
                    logging.info("Returning cached return value for '%s'"%(key))
                return cached
            except KeyError:
                logging.debug("Computing value for '%s'"%(key))
                ret = f(*args, **kwargs)
                cache_object[key] = ret
                if cache_do_logging:
                    logging.info("Caching return value for '%s'"%(key))
                return ret
        return g
    
    # if we got PureFunction, the returned function should also be pure
    # please see the PureFunction.__doc__
    if isinstance(fun, PureFunction):
        g = g_factory(fun)
        functools.update_wrapper(g, fun.f)
        return PureFunction(g)
    
    return functools.wraps(fun)(g_factory(fun))
    
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    
    init_cache(filename=':memory:', expires=0.1, log=True)
    
    @cache_result
    @declare_pure_function
    def add(a, b):
        return a + b
    
    @cache_result
    @declare_pure_function
    def bla(f):
        return f(10)
    
    @cache_result
    @declare_pure_function
    def multmap(l):
        return ( reduce( (lambda x, y: x*y) , l), time.time() )
    
    def test1():
        multmap([1,2,3])
        time.sleep(0.1)
        multmap([1,2,3])
        time.sleep(0.1)
        multmap([1,2,3])
        time.sleep(0.1)
        multmap([1,2,3])
        time.sleep(0.1)
        bla(lambda x : x + 10)
        f=lambda x : x + 10
        bla(f)
        
    def test2():
        """Stateless (pure) class and a pure function as arguments"""
        
        class Adder:
            """ The Adder must be `stateless` in a sense that results
            of __call__ will always produce the same results for the
            same args.  Moreover the Adder must have __repr__ which has
            all the information to uniquely define the Adder instance -
            once again, so that the statement about __call__ holds."""
            def __init__(self, offset):
                self.offset = offset
            def __call__(self, a, b=10):
                return a + self.offset
            def __repr__(self):
                return "Adder(offset=%s)"%self.offset
        a = Adder(2)
        
        @cache_result
        @declare_pure_function
        def my_map(f, l):
            return map(f, l)
        
        my_map(a, range(10))
        my_map(a, range(10))
        
        @declare_pure_function
        def multiplicator(x, mult=2):
            return x * mult 
        
        my_map(multiplicator, range(10))
        
        from utils import partial, partial_right
        
        my_map(partial_right(multiplicator, 2), range(10))
        my_map(partial(a, 2), range(10))
        my_map(partial_right(multiplicator, 2), range(10))
        my_map(partial(a, 2), range(10))
        
    def test3():
        import utils
        
        @cache_result
        @declare_pure_function
        def bla(f):
            return f(10)
        
        @cache_result
        #@utils.declare_pure_function
        def h(x):
            return 2 * x
        
        h(10)
        print 
        bla(h)
        #for f in [h,
        #          declare_pure_function(h),
        #          cache_result(h),
        #          )]:
        #    print f(10), f, type(f)
        #    print
    
        
        return
        
    def test5():
        class Adder:
            def __init__(self, offset):
                self.offset = offset
                
            def __call__(self, a, b=10):
                return a + self.offset
            
            def __repr__(self):
                return "Adder(offset=%s)"%self.offset
        
        #Adder.__call__ = cache_result(declare_pure_function(Adder.__call__))
            
        a = Adder(2)        
        a(20)
        print repr(a.__call__)
        
        return
        
        @cache_result
        @declare_pure_function
        def tralala(a, c, b=10):
            return -20
        
        print tralala(a, 1)
            
        
    def test6():
        multmap([1,2,3])
        multmap([1,2,3, 4])
        multmap([1,2,3])
        _print_all()
        time.sleep(0.5)
        multmap([1,2,3])
        _print_all()
        delete_expired()
        _print_all()
        
        
    test6()
    #test2()
        