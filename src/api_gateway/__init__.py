import json

from nameko.exceptions import RemoteError
from nameko.rpc import RpcProxy
from nameko.web.handlers import http
from lib.nameko_cors import cors_http

class ApiGatewayService:
    name = 'api_gateway'

    patient_rpc = RpcProxy('patient_service')
    physician_rpc = RpcProxy('physician_service')

    @http('GET', '/healthy')
    def healthy(self, request):
        return json.dumps({'healthy': True})

    @cors_http('POST', '/patient_reg')
    def patient_register_hospital(self, request):
        data = json.loads(request.get_data(as_text=True))
         try:
            card = self.patient_rpc.register(patient_name=data['name'], patient_id=data['id'])
            return json.dumps({'success': True, 'card': card})
        except RemoteError as e:
            return 500, json.dumps({'success': False, 'error': str(e)})
    
    @cors_http('POST', '/patient_read')
    def patient_read_hospital(self, request):        
        data = json.loads(request.get_data(as_text=True))
        success = self.patient_rpc.read(patient_uid=data['uid'])
        return json.dumps({'success': success})
    
    @cors_http('POST', '/physician_reg')
    def physician_register_hospital(self, request):
        data = json.loads(request.get_data(as_text=True))
        success = self.physician_rpc.register(physician_name=data['name'], physician_id=data['id'])
        return json.dumps({'success': success})

    @cors_http('POST', '/physician_read')
    def physician_read_hospital(self, request):
        data = json.loads(request.get_data(as_text=True))
        success = self.physician_rpc.read(patient_uid=data['uid'])
        return json.dumps({'success': success})

    @cors_http('POST', '/physician_write')
    def physician_write_hospital(self, request):
        data = json.loads(request.get_data(as_text=True))
        success = self.physician_rpc.write(physician_id=data['phys_id'], patient_uid=data['patient_uid'], data=data['data'])
        return json.dumps({'success': success})
