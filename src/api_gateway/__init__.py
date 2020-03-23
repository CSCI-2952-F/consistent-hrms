import json

from nameko.rpc import RpcProxy
from nameko.web.handlers import http


class ApiGatewayService:
    name = 'api_gateway'

    patient_rpc = RpcProxy('patient_service')
    physician_rpc = RpcProxy('physician_service')

    @http('GET', '/healthy')
    def healthy(self, request):
        return json.dumps({'healthy': True})

    @http('POST', '/patient')
    def patient_register_hospital(self, request):
        data = json.loads(request.get_data(as_text=True))
        success = self.patient_rpc.register(patient_id=data['id'], public_key=data['public_key'])
        return json.dumps({'success': success})
