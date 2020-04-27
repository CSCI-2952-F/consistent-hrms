import json
import os

from nameko.exceptions import RemoteError, safe_for_serialization
from nameko.rpc import RpcProxy
from werkzeug.wrappers import Response

from api_gateway.discovery_svc import DiscoveryService
from lib.nameko_cors import CorsHttpRequestHandler


class HttpEntrypoint(CorsHttpRequestHandler):
    def response_from_exception(self, exc):
        text = json.dumps({
            'success': False,
            'error': safe_for_serialization(exc),
        })

        response = Response(text, status=500, mimetype='application/json')
        return response


http = HttpEntrypoint.decorator

DISCOVERY_GRPC_ADDR = os.getenv('DISCOVERY_GRPC_ADDR')
if not DISCOVERY_GRPC_ADDR:
    raise Exception('DISCOVERY_GRPC_ADDR not set')


class ApiGatewayService:
    name = 'api_gateway'

    patient_rpc = RpcProxy('patient_service')
    physician_rpc = RpcProxy('physician_service')
    discovery_svc = DiscoveryService(DISCOVERY_GRPC_ADDR)

    @http('GET', '/healthy')
    def healthy(self, _):
        return json.dumps({'healthy': True})

    @http('POST', '/patient_reg')
    def patient_register_hospital(self, request):
        data = json.loads(request.get_data(as_text=True))
        uid = self.patient_rpc.register(patient_name=data['name'], patient_id=data['id'], pub_key=data['pub_key'])
        return json.dumps({'success': True, 'uid': uid})

    @http('POST', '/patient_read')
    def patient_read_hospital(self, request):
        data = json.loads(request.get_data(as_text=True))
        res = self.patient_rpc.read(patient_uid=data['uid'])
        return json.dumps({'success': True, 'data': res})

    @http('POST', '/patient_unreg')
    def patient_unregister_hospital(self, request):
        data = json.loads(request.get_data(as_text=True))
        success = self.patient_rpc.unregister(patient_uid=data['uid'], auth_token=data['auth_token'])
        return json.dumps({'success': success})

    @http('POST', '/patient_transfer')
    def patient_transfer_hospital(self, request):
        data = json.loads(request.get_data(as_text=True))
        success = self.patient_rpc.transfer(patient_uid=data['uid'], auth_token=data['auth_token'], dest_hospital=data['dest_hospital'])
        return json.dumps({'success': success})

    @http('POST', '/physician_reg')
    def physician_register_hospital(self, request):
        data = json.loads(request.get_data(as_text=True))
        success = self.physician_rpc.register(physician_name=data['name'], physician_id=data['id'])
        return json.dumps({'success': success})

    @http('POST', '/physician_read')
    def physician_read_hospital(self, request):
        data = json.loads(request.get_data(as_text=True))
        res = self.patient_rpc.read(patient_uid=data['uid'])
        return json.dumps({'success': True, 'data': res})

    @http('POST', '/physician_write')
    def physician_write_hospital(self, request):
        data = json.loads(request.get_data(as_text=True))
        success = self.physician_rpc.write(physician_uid=data['phys_uid'], patient_uid=data['patient_uid'], data=data['data'])
        return json.dumps({'success': success})

    @http('GET', '/list_hospitals')
    def list_hospitals(self, _):
        hospitals = self.discovery_svc.list_hospitals()
        return json.dumps(hospitals)
