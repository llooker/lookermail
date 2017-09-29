###### EMAIL IMPORTS #####
import smtplib,  datetime, time, os, logging
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.Utils import COMMASPACE, formatdate
from email import generator
from email import Encoders
import jinja2
import codecs
import ConfigParser
import json
from collections import namedtuple
import lib.helpers as h
from lib.apiClient import lookerAPIClient

config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('configs/config.txt')

class emailClient:
    def __init__(self, conf, dataSources, pathIndex): 
        self.conf         = conf
        self.sendAs       = conf.sendAs
        self.sendTo       = conf.to
        self.subject      = conf.subject
        
        self.template     = conf.template
        self.dataSources  = dataSources
        self.sendToCC     = conf.cc
        
        self.pathIndex    = pathIndex

        self.msg          = MIMEMultipart('alternative')
        self.html         = self.bindDataToTemplate()
        self.text         = ''

        self.msg['From'] = self.sendAs
        self.msg['To'] = COMMASPACE.join(self.sendTo)
        self.msg['Cc'] = COMMASPACE.join(self.sendToCC)
        self.msg['Date'] = formatdate(localtime=True)
        self.msg['Subject'] = self.subject

        self.msg.attach( MIMEText(self.text, 'plain'))
        self.msg.attach( MIMEText(self.html.encode('UTF-8'), 'html'))


    def bindAttachments(self):
        for f in self.conf.dataSources:
            if f.dataType != 'json':
                part = MIMEBase('application', "octet-stream")
                part.set_payload( open(self.pathIndex[f.templateVariableName],"rb").read() )
                Encoders.encode_base64(part)
                ######### IMPORTANT:::: Change the content disposition back ######### 
                if f.display == 'inline' :
                    part.add_header('Content-Disposition', 'inline; filename="%s"' % os.path.basename(self.pathIndex[f.templateVariableName]))  
                    part.add_header('Content-ID','<' + f.templateVariableName + '>')
                else:
                    part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(self.pathIndex[f.templateVariableName])) 
                self.msg.attach(part)

    def bindDataToTemplate(self):
        templateLoader = jinja2.FileSystemLoader(searchpath = "templates/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template( self.template )
        variableDictionary = self.conf.variables._asdict()
        dataSourceDictionary = self.conf.dataSources._asdict()
        variableDictionary.update(dataSourceDictionary)
        variableDictionary.update(self.dataSources)
        logging.debug(variableDictionary)
        return template.render( variableDictionary )

    def send(self):
        # uncomment the next 4 lines to actually send
        smtp = smtplib.SMTP_SSL(config.get('smtp', 'host'), config.getint('smtp', 'port'))
        smtp.ehlo()
        smtp.login(config.get('smtp', 'username'), config.get('smtp', 'password'))
        smtp.sendmail(self.sendAs, h.removeDupes(self.sendTo + self.sendToCC), self.msg.as_string()) #potentially remove dupes between to and cc fields (see example code)
        smtp.close()
        return [self.msg,self.html]

class reportBuilder:
    def __init__(self,report,instanceid):
        '''
            Pulls up the report json config based on the report argument (brought in from the command line argument).
            It auto-binds those properties into an instnace level 'config' attribute
            '''
        with open('configs/reports/' + report + '.json') as data_file:    
            self.config = json.loads(data_file.read(), object_hook=lambda d: namedtuple('obj', d.keys())(*d.values()))

        self.lookerAPI = lookerAPIClient(
            api_host      = config.get('api', 'host'), 
            api_client_id = config.get('api', 'client_id'), 
            api_secret    = config.get('api', 'secret'), 
            api_port      = config.get('api', 'port')
        )
        self.report = report
        self.instanceID = instanceid
        self.messageid = 1 ## TODO implement a counter for the one to many relationship that will emerge when I create per recipient filters
        self.dataSources = {}
        self.path = ''
        self.pathIndex = {}

    def writeFile(self, name, content ,extension=".html",mode="wb",encoding="utf-8"):
        f = codecs.open(self.path + '/' + name + extension, mode, encoding)
        f.write( content )
        f.close()

    def writeEmail(self, name, content ,extension=".eml",mode="w"):
        with open(self.path + '/' + name + extension, mode) as outfile:
            gen = generator.Generator(outfile)
            gen.flatten(content)
        

    def buildDirectory(self):
        self.path = 'sentArchive/' + \
                    self.config.reportName + '_' +\
                    time.strftime("%m-%d-%Y_%I%M%p") + \
                    '_instance_' + str(self.instanceID) + \
                    '_msg_' + str(self.messageid)
        os.mkdir( self.path, 0755 )

    def buidDataSources(self):
        self.buildDirectory()

        for ds in self.config.dataSources:
            if ds.lookerType == 'look':
                if ds.dataType == 'json':
                    self.dataSources[ds.templateVariableName] = self.lookerAPI.runLook(ds.location,responseType=ds.dataType)
                else:
                    self.dataSources[ds.templateVariableName] = self.lookerAPI.runLook(ds.location,responseType=ds.dataType)
                    tmpFilePath = self.path+'/'+ds.templateVariableName + '.' + ds.dataType
                    tmpFile = open(tmpFilePath,'wb')

                    self.dataSources[ds.templateVariableName].raw.decode_content = True
                    for chunk in self.dataSources[ds.templateVariableName]:
                        tmpFile.write(chunk)
                    tmpFile.close()
                    # print self.dataSources[ds.templateVariableName]
                    self.pathIndex[ds.templateVariableName] = tmpFilePath
            else:
                if ds.dataType == 'json':
                    self.dataSources[ds.templateVariableName] = self.lookerAPI.inlineQuery(ds.location,responseType=ds.dataType)
                else:
                    self.dataSources[ds.templateVariableName] = self.lookerAPI.inlineQuery(ds.location,responseType=ds.dataType)
                    tmpFilePath = self.path+'/'+ds.templateVariableName + '.' + ds.dataType
                    tmpFile = open(tmpFilePath,'wb')

                    self.dataSources[ds.templateVariableName].raw.decode_content = True
                    for chunk in self.dataSources[ds.templateVariableName]:
                        tmpFile.write(chunk)
                    tmpFile.close()
                    self.pathIndex[ds.templateVariableName] = tmpFilePath


    def build(self):
        self.buidDataSources()
        emInstance = emailClient(self.config,self.dataSources, self.pathIndex)
        emInstance.bindAttachments()
        archive = emInstance.send()
        self.writeFile('plain',archive[1])
        self.writeEmail('mime',archive[0],extension='.eml')
        

