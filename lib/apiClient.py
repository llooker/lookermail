#Very Basic Looker API class allowing us to access the data from a given Look ID
import requests, logging, json, time
import lib.helpers as h

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
        # response = requests.post(self.uri_full + call, headers=self.auth_headers, data=json_payload)
        # important: the json argument automatically calls json dumps on the dict you pass it
        return response

    def get(self, call=''):
        h.logMultipleDebug([["FULL URI: ",self.uri_full + call]])
        response = requests.get(self.uri_full + call, headers=self.auth_headers)
        return response

    @h.timeit
    def runLook(self, look, responseType='json', limit=100):
        assert responseType in ['json', 'json_detail','jpg','png','csv','xlsx','sql'], 'responseType not json, jpg, png, csv, xlsx, sql'
        optional_arguments = '?' + 'limit=' + str(limit)
        if responseType in ['json','json_detail']:
            response = self.get('/'.join(['looks',look,'run',responseType])+optional_arguments)
            h.logMultipleDebug([
                    ["Request URL:",response.request.url],
                    ["Request Headers:",response.request.headers],
                    ["Request Payload:",response.request.body],
                    ["Response URL:",response.url],
                    ["Response Code:",response.status_code],
                    ["Response Headers:",response.headers],
                    ["Response Payload:",response.text],
                        ]) 
            return response.json()
        else:
            response = self.get('/'.join(['looks',look,'run',responseType])+optional_arguments)
            h.logMultipleDebug([
                    ["Request URL:",response.request.url],
                    ["Request Headers:",response.request.headers],
                    ["Request Payload:",response.request.body],
                    ["Response URL:",response.url],
                    ["Response Code:",response.status_code],
                    ["Response Headers:",response.headers],
                    ["Response Payload:",response],
                        ]) 
            return response

    @h.timeit
    def inlineQuery(self, queryConfig, limit=100, responseType='json', filter_value={}):
        assert responseType in ['json','json_detail','jpg','png','csv','xlsx','sql','pdf'], 'responseType not json, jpg, png, csv, xlsx, sql, pdf'
        
        optionalArguments = '&' + 'limit=' + str(limit) + '&' + 'server_table_calcs=true'
        # pay = open('configs/queries/' + queryConfig + '.json', 'r').read()
        pay = json.loads(open('configs/queries/' + queryConfig + '.json', 'r').read())
        if filter_value:
            # print(pay)
            # for k,v in filter_value.items():
            pay["filters"].update(dict(filter_value))
        # print(pay)
        # pay = json.dumps(pay)
        if responseType in ['json','json_detail']:
            response = self.post(call='queries/run/'+responseType+'?force_production=true' + optionalArguments, json_payload=pay)
            h.logMultipleDebug([
                    ["Request URL:",response.request.url],
                    ["Request Headers:",response.request.headers],
                    ["Request Payload:",pay],
                    ["Response URL:",response.url],
                    ["Response Code:",response.status_code],
                    ["Response Headers:",response.headers],
                    ["Response Payload:",response.text],
                        ])
            # logging.debug(response.request.url)
            # logging.debug(response.request.headers)
            # logging.debug("Request Payload: " + pay)
            # logging.debug(response.url)
            # logging.debug(response.headers)
            # logging.debug(response.text)
            
            return response.json()
        else:
            response = self.post(call='queries/run/'+responseType+'?force_production=true' + optionalArguments, json_payload=pay)
            h.logMultipleDebug([
                    ["Request URL:",response.request.url],
                    ["Request Headers:",response.request.headers],
                    ["Request Payload:",pay],
                    ["Response URL:",response.url],
                    ["Response Code:",response.status_code],
                    ["Response Headers:",response.headers],
                    ["Response Payload:",response],
                        ])
            return response

    def queueDashboard(self,dashboard_id,result_format='pdf',width=1200,height=2500):
        '''
            post to /render_tasks/dashboards/{dashboard_id}/{result_format}
            obtains the render task id
            Works for both lookml dashboards and udds based on a try catch
        '''
        def RepresentsInt(s):
            try: 
                int(s)
                return True
            except ValueError:
                return False
        lookMLDashboardCallPath = 'lookml_dashboards'
        if RepresentsInt(dashboard_id):
            lookMLDashboardCallPath = 'dashboards'

        optional_arguments = '?' + 'width='+ str(width) + '&height=' + str(height) 
        pay = {
            "dashboard_style": "tiled",
            "dashboard_filters": ""
        }
        response = self.post(call='render_tasks/'+lookMLDashboardCallPath+'/'+dashboard_id+'/'+result_format + optional_arguments ,json_payload=pay)
        h.logMultipleDebug([
                    ["Request URL:",response.request.url],
                    ["Request Headers:",response.request.headers],
                    ["Request Payload:",pay],
                    ["Response URL:",response.url],
                    ["Response Code:",response.status_code],
                    ["Response Headers:",response.headers],
                    ["Response Payload:",response.text],
                        ])
        return response.json()


    def pingRenderTask(self,render_task_id):
        response = self.get(call='render_tasks/'+render_task_id)
        responseJson = response.json()
        status = responseJson['status']
        return status

    def fetchRenderedDashboard(self,render_task_id):
        '''
            post to /render_tasks/{render_task_id}/results 
            provides the reder task id, then fetches the result which can be used as a file
        '''
        status = self.pingRenderTask(render_task_id) 
        logging.info('initial dashboard status:' + status)
        while status == 'rendering':
            time.sleep(5)
            logging.info("status is ...." + status)
            status = self.pingRenderTask(render_task_id) 
            if status != 'rendering':
                break
        response = self.get(call='render_tasks/'+render_task_id+'/results')

        return response

    def dash(self,dashboard_id,result_format='pdf',width=1200,height=2500):
        queueTicket = self.queueDashboard(dashboard_id,result_format=result_format,width=width,height=height)
        h.logMultipleDebug([["QueueTikcet",queueTicket['id']]])
        response = self.fetchRenderedDashboard(queueTicket['id'])
        return response
