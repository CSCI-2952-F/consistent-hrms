import json

from nameko.exceptions import RemoteError
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

        try:
            card = self.patient_rpc.register(patient_name=data['name'], patient_id=data['id'])
            return json.dumps({'success': True, 'card': card})
        except RemoteError as e:
            return 500, json.dumps({'success': False, 'error': str(e)})
