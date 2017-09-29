#Very Basic Looker API class allowing us to access the data from a given Look ID
import requests, logging
import helpers as h

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
        logging.debug(response.request.headers)
        logging.debug(response.request.url)
        logging.debug(response.headers)
        logging.debug(response.content)
        return response

    def get(self, call=''):
        response = requests.get(self.uri_full + call, headers=self.auth_headers)
        return response
    
    @h.timeit
    def runLook(self, look, responseType='json', limit=100):
        assert responseType in ['json','jpg','png','csv','xlsx','sql'], 'responseType not json, jpg, png, csv, xlsx, sql'
        optional_arguments = '?' + 'limit=' + str(limit)
        if responseType == 'json':
            return self.get('/'.join(['looks',look,'run',responseType])+optional_arguments).json()
        else:
            return self.get('/'.join(['looks',look,'run',responseType])+optional_arguments)

    @h.timeit
    def inlineQuery(self, queryConfig, limit=100, responseType='json', filter_value=""):
        assert responseType in ['json','jpg','png','csv','xlsx','sql'], 'responseType not json, jpg, png, csv, xlsx, sql'
        
        optionalArguments = '&' + 'limit=' + str(limit)
        pay = open('configs/queries/' + queryConfig + '.json', 'r').read()
        logging.debug(pay)
        return self.post(call='queries/run/'+responseType+'?force_production=true' + optionalArguments, json_payload=pay)