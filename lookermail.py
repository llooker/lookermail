#!/usr/bin/env python

#########
# Author : Russell Garner, russell@looker.com
# Date: 2017-09-25
# Description: This is a package for configuring and sending HTML emails using Looker API Data
# for further details please refer to the package README
#########

###### SYSTEM IMPORTS #####
import os, re, sys, logging, traceback, traceback, time, datetime

import operator
from operator import itemgetter

## Custom Imports
import lib.helpers as h
# from lib.apiClient import lookerAPIClient 
from lib.emailClient import reportBuilder

# optional if you're intending to execute from a remote directory when cronning: 
# os.chdir(os.path.dirname(os.path.abspath(__file__)))



######### Runtime Management #########
class executionManager:
    def __init__(self):
        h.Settings()                  #Instantiate Global Settings
        self.logging_level      = h.settings.config.getint('general','logging_level')
        self.ts                 = time.time()
        self.te                 = time.time()
        self.executionCounter   = self.instanceSerial()
        global instanceSerialValue
        instanceSerialValue     = self.executionCounter
        self.initializeLogging()    #Begin Logging Stream
        self.welcomeMessage()       #Print Welcome Message
        h.globalExecutionData()       #Instantiate Global runtime data

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
                            level=self.logging_level)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(self.logging_level)
        formatter = logging.Formatter(
                                      '%(levelname)s:%(asctime)s %(message)s', 
                                      datefmt='%m/%d/%Y %I:%M:%S %p')
        ch.setFormatter(formatter)
        logging.getLogger('').addHandler(ch)
        self.logger = logging.getLogger('')

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

    def close(self):
        self.te = time.time()
        self.logger.info('total execution took: %4.4f sec' % (self.te-self.ts,))
        self.logger.info('-'*21 + ' END INSTANCE #' + self.executionCounter + '-'*21)
    def run(self):
        myReport = reportBuilder(h.settings.report, self.executionCounter)
        myReport.build()
######### Invoke Execution Steps #########
if __name__ == '__main__':
    instance = executionManager()
    instance.run()
    instance.close()
######### End Execution Steps #########