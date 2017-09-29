#!/usr/bin/env python

#########
# Author : Russell Garner, russell@looker.com
# Date: 2017-09-25
# Description: This is a package for configuring and sending HTML emails using Looker API Data
# for further details please refer to the package README
#########

###### SYSTEM IMPORTS #####
import os, re, sys, logging, traceback, traceback, time, dateutil.parser, datetime
import ConfigParser, argparse
import operator
from operator import itemgetter

## Custom Imports
import lib.helpers as h
# from lib.apiClient import lookerAPIClient 
from lib.emailClient import reportBuilder

# optional if you're intending to execute from a remote directory when cronning: 
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

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


######### Runtime Management #########
class executionManager:
    def __init__(self):
        Settings()                  #Instantiate Global Settings
        self.logging_level      = settings.config.getint('general','logging_level')
        self.ts                 = time.time()
        self.te                 = time.time()
        self.executionCounter   = self.instanceSerial()
        global instanceSerialValue
        instanceSerialValue     = self.executionCounter
        self.initializeLogging()    #Begin Logging Stream
        self.welcomeMessage()       #Print Welcome Message
        globalExecutionData()       #Instantiate Global runtime data


    def __str__(self):
        return 'Lookermail Execution Instance #: ' + self.executionCounter

    def instanceSerial(self):
        counterLocation = 'logs/instance_serial'
        try:
            executionCounterFile = open(counterLocation,'r')
            executionCounter = int(executionCounterFile.read())
            executionCounter = str(executionCounter + 1)
            executionCounterFile = open(counterLocation,'w')
            executionCounterFile.write(executionCounter)
            executionCounterFile.close()
            return executionCounter
        except:
            if os.path.exists(counterLocation):
                pass
            else:
                executionCounterFile = open(counterLocation,'w')
                executionCounterFile.write('0')
            return str(0)

    def initializeLogging(self):
        logging.basicConfig(
                            filename='logs/log.log', 
                            format='%(levelname)s:%(asctime)s %(message)s', 
                            datefmt='%m/%d/%Y %I:%M:%S %p', 
                            level=logging.INFO)
        ch = logging.StreamHandler(sys.stdout)
        ch2 = logging.StreamHandler(sys.stdout)
        ch.setLevel(self.logging_level)
        ch2.setLevel(logging.INFO)
        formatter = logging.Formatter(
                                      '%(levelname)s:%(asctime)s %(message)s', 
                                      datefmt='%m/%d/%Y %I:%M:%S %p')
        ch.setFormatter(formatter)
        ch2.setFormatter(formatter)
        logging.getLogger('').addHandler(ch)
        self.logger = logging.getLogger('test')
        self.logger.addHandler(ch2)
        global logMe
        logMe = self.logger

    def welcomeMessage(self):
        self.logger.info('-'*21 + ' START INSTANCE #' + self.executionCounter + '-'*21)
        self.logArgs()
        self.logger.info(
            #Start Coloriztion # \u001b[47;1m\u001b[35;1m
        u'''
            |  _  _ |  _ ._|\/| _.o| 
            |_(_)(_)|<(/_| |  |(_||| 
            Version 1.0              '''
            #End Colorizarion # \u001b[0m
        )
    def logArgs(self):
        argList = ''
        for elem in sys.argv:
            argList = argList + ' ' + elem
        self.logger.info(argList)
        return argList

    def exitWithError(self,errorText=''):
        if errorText:
            logging.info(errorText)
        self.te = time.time()
        self.logger.info('Total CalendarETL execution took: %4.4f sec' % (self.te-self.ts,))
        self.logger.info('-'*21 + ' END INSTANCE #' + self.executionCounter + '-'*21)
        sys.exit(1)

    def close(self):
        self.te = time.time()
        self.logger.info('total execution took: %4.4f sec' % (self.te-self.ts,))
        self.logger.info('-'*21 + ' END INSTANCE #' + self.executionCounter + '-'*21)
    def run(self):
        myReport = reportBuilder(settings.report, self.executionCounter)
        myReport.build()
######### Invoke Execution Steps #########
instance = executionManager()
instance.run()
instance.close()
######### End Execution Steps #########