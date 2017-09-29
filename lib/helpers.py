### Global, Static, Classless Helpers ###
import time,logging


def removeDupes(seq): 
   # Not order preserving
   keys = {}
   for e in seq:
       keys[e] = 1
   return keys.keys()

def timeit(f):
    '''
        Run @timeit function(arg1,...) to log a time associated with any function call
        '''
    def timed(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        logging.info('func:%r args:[%r, %r] took: %4.4f sec' % (f.__name__, args, kw, te-ts))
        # logging.info('func:%r args:[%r, %r] took: %4.4f sec' % (f.__name__, args, kw, te-ts))
        return result
    return timed

