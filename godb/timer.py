import time
import math
import logging

class Timer:
    """Class for measuring lenghts of nested time intervals.
    Intervals are opened either like:
    
    >>> t = Timer()
    >>> t.start()
    >>> do_stuff()
    >>> t.stop()
    
    Or using the with statement:
    
    >>> with t():
           do_stuff()
    """
    def __init__(self):
        self.times = []        
        self.next_args = {}
        
    def start(self):
        """Opens time interval."""
        self.times.append((time.time(), [], self.next_args))
        self.next_args = {}
        
    def stop(self):
        """Closes time interval. Returns tuple (duration, avg_child_duration)."""
        now = time.time()
        my_start, children_durations, _ = self.times[-1]
        del self.times[-1]
        
        my_duration = now - my_start
        # add duration of this object to the parent list
        if self.times:
            self.times[-1][1].append(my_duration)
            
        return (my_duration, children_durations)
        
    def stop_n_log(self, comment='  time elapsed', child_name='child'):
        total, children = self.stop()
        msg = "%s: %.3f s"%(comment, total)
        if children:
            c_sum, c_len = sum(children), len(children)
            mean = c_sum / c_len
            sd = 0
            if c_len > 1:
                sd = math.sqrt(sum( (val - mean)**2 for val in children ) / (c_len - 1))
            msg += """, time not spent in children (overhead) %.3f s = %.2f%%
  #%d x %s took %.3f s:
  mean: %.3f s (sd = %.3f s)"""%(
                total - c_sum, 100.0 * (total - c_sum) / total,
                c_len, child_name, c_sum, mean, sd)
        logging.info(msg + '\n')
        
    def stop_arg(self):
        _, _, kwargs = self.times[-1]
        log = kwargs.pop('log', False)
        if log:
            return self.stop_n_log(**kwargs)
        return self.stop()
        
    def __call__(self, **kwargs):
        self.next_args = kwargs
        return self
    
    def __enter__(self):
        self.start()
        
    def __exit__(self, *args):
        self.stop_arg()        
        
import random

def test():
    t = Timer()    
        
    t.start()
    with t(log=True, comment='test loop 1', child_name='blabla'):
        for a in xrange(1000):
            with t():
                time.sleep(random.random()/20000)
                
    # eq to
    with t(log=True, comment='test loop 2', child_name='blabla2'):
        for a in xrange(1000):
            t.start()
            time.sleep(random.random()/20000)
            t.stop()
            
    t.stop_n_log(child_name='test loop')
                

if "__main__" == __name__:
    logging.getLogger().setLevel(logging.INFO)
    test()
        
    