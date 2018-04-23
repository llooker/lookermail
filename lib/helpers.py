### Global, Static, Classless Helpers ###
import time,logging
try:
    #Python 2.x
    import ConfigParser as ConfigParser
except:
    #Python 3.x
    import configparser as ConfigParser

import argparse

######### Settings and Singletons #########
class Arguments:
    '''Serves as a wrapper for aruments, argument flags are set globally upon class instantiation'''
    def __init__(self):
        parser = argparse.ArgumentParser()
        #db params
        parser.add_argument("-r", "--report", help="Name the report configuration to send", type=str)
        global args 
        args = parser.parse_args()

class Settings:
    def __init__(self):
        Arguments()
        self.config = ConfigParser.RawConfigParser(allow_no_value=True)
        self.config.read('configs/config.txt')
        self.report = args.report
        #Example of the of overriding a config file setting with a command line switch
        # if args.example:
        #     self.example = args.example
        # else:
        #     self.example = self.config.get('log_section', 'example')
        global settings
        settings = self

class globalExecutionData:
    '''
        Put any data global runtime variables into this class to help encapsulate global variables as much as possible
        '''
    def __init__(self):
        self.msgCounter = 0
        global runtimeData
        runtimeData = self
    
    def msgIDPlusOne(self):
        '''
            Allows for the incrmenting of Message IDs across email class instances
            '''
        self.msgCounter = self.msgCounter + 1
        return str(self.msgCounter)

def logMultipleDebug(msgs):
    '''
        Allow rich multi-object debugging logs by passing a list of lists with message calls
        logMultipleDebug([["header:",request.header],["payload:",request.payload]])
        '''
    for msg in msgs:
        logging.debug(' '.join([msg[0],str(msg[1])]))


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

