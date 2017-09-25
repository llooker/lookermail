#!/usr/bin/env python
import requests
import ConfigParser

#Read config file with Looker API and Database connection information
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



class execution:
    def __init__(self):
        print 'Execution Initiated'

    def run(self):
        x = lookerAPIClient(
            api_host      = config.get('api', 'api_host'), 
            api_client_id = config.get('api', 'api_client_id'), 
            api_secret    = config.get('api', 'api_secret'), 
            api_port      = config.get('api', 'api_port')
        )
        historicalCustomers = x.runLook('292',limit=10000)
        newCustomers = x.runLook('293',limit=10000)
        print historicalCustomers


instance = execution()
instance.run()