#!/usr/bin/env python
import requests
import ConfigParser

###### EMAIL IMPORTS #####
import smtplib, os, sys, datetime, time
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import jinja2
import codecs

#Read config file with Looker API and SMTP gateway information
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('configs/config.txt')

#Very Basic Looker API class allowing us to access the data from a given Look ID
class lookerAPIClient:
    def __init__(self, api_host=None, api_client_id=None, api_secret=None, api_port='19999'):
        auth_request_payload = {'client_id': api_client_id, 'client_secret': api_secret}
        self.host = api_host
        self.uri_stub = '/api/3.0/'
        self.uri_full = ''.join([api_host, ':', api_port, self.uri_stub])
        response = requests.post(self.uri_full + 'login', params=auth_request_payload)
        authData = response.json()
        self.access_token = authData['access_token']
        self.auth_headers = {
                'Authorization' : 'token ' + self.access_token,
                }

    def post(self, call='', json_payload=None):
        response = requests.post(self.uri_full + call, headers=self.auth_headers, json=json_payload)
        return response.json()

    def get(self, call=''):
        response = requests.get(self.uri_full + call, headers=self.auth_headers)
        return response.json()

    def runLook(self, look, limit=100):
        optional_arguments = '?' + 'limit=' + str(limit)
        return self.get('/'.join(['looks',look,'run','json'])+optional_arguments)


class email:
    def __init__(self):
        print 'email class instantiated'

    def send_html_mail(self, send_from, send_to, subject, html, files=[], send_to_cc=[]):
        assert type(send_to)==list
        assert type(files)==list
        text = ''
        msg = MIMEMultipart('alternative')
        msg['From'] = send_from
        msg['To'] = COMMASPACE.join(send_to)
        msg['Cc'] = COMMASPACE.join(send_to_cc)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject

        msg.attach( MIMEText(text, 'plain'))
        msg.attach( MIMEText(html.encode('UTF-8'), 'html'))
        
        for f in files:
            part = MIMEBase('application', "octet-stream")
            part.set_payload( open(f,"rb").read() )
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
            msg.attach(part)

        # smtp = smtplib.SMTP(server)
        smtp = smtplib.SMTP_SSL(config.get('smtp', 'host'), config.getint('smtp', 'port'))
        # smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.ehlo()
        smtp.login(config.get('smtp', 'username'), config.get('smtp', 'password'))
        # smtp.starttls()
        # smtp.sendmail(send_from, lib.modules.abstract.removeDupes(send_to + send_to_cc), msg.as_string())
        smtp.sendmail(send_from, send_to + send_to_cc, msg.as_string())
        smtp.close()

    def build_message(self, TEMPLATE_FILE, templateVars):
        templateLoader = jinja2.FileSystemLoader(searchpath = "templates/")
        # templateLoader = jinja2.FileSystemLoader(searchpath = os.getcwd() + "/lib/templates/") ## Original Line
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template( TEMPLATE_FILE )
        return template.render( templateVars )

class execution:
    def __init__(self):
        print 'Execution Initiated'

    def run(self):
        lookerAPIInstance = lookerAPIClient(
            api_host      = config.get('api', 'host'), 
            api_client_id = config.get('api', 'client_id'), 
            api_secret    = config.get('api', 'secret'), 
            api_port      = config.get('api', 'port')
        )
        basicTotal = lookerAPIInstance.runLook('299',limit=10000)
        clientSummary = lookerAPIInstance.runLook('349',limit=10000)
        emailCoordinatorInstance = email()
        # message_variables = {
        # "SENDDATE":time.strftime("%m/%d/%Y"),
        # "URLDATE":time.strftime("%m-%d-%Y"),
        # "MESSAGETITLE":'Hello World!',
        # "MESSAGETEXT":'message with good news!',
        # }
        # testfile = codecs.open('cool.html','w',"utf-8")
        # testfile.write( y.build_message('default.html',message_variables) )
        templateVars = {
        "SENDDATE":time.strftime("%m/%d/%Y"),
        "URLDATE":time.strftime("%m-%d-%Y"),
        "MESSAGETITLE":'Donation Report',
        "MESSAGETEXT":'Donation Report Body Text',
        "clients":clientSummary,
        "basictotal":basicTotal
        }
        emailCoordinatorInstance.send_html_mail(
            'russell@looker.com', #from 
            ['russelljgarner@gmail.com'], #to
            'Daily Donation and Volunteer Report', #subject line
            emailCoordinatorInstance.build_message("donation_report/donation_report.html",templateVars), #Template Variables
            [] #Attachements (optional)
        )
        # emailCoordinatorInstance.simpleNotice('hello from lookermail script',historicalCustomers[0]['ltv_predictions.sum_ltv_prediction'],'Test',['russelljgarner@gmail.com'])
        # testfile.close()

instance = execution()
instance.run()