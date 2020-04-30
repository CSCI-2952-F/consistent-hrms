from datetime import datetime

import grpc

from lib.discovery_svc.pb.discovery_pb2 import *
from lib.discovery_svc.pb.discovery_pb2_grpc import HospitalDiscoveryStub

GRPC_ADDR = 'discovery_service:8080'


class DiscoveryService:
    def __init__(self):
        channel = grpc.insecure_channel(GRPC_ADDR)
        self.client = HospitalDiscoveryStub(channel)

    def get_id(self) -> str:
        req = InfoRequest()
        res = self.client.GetInfo(req)

        return res.id

    def get_private_key(self) -> str:
        req = InfoRequest()
        res = self.client.GetInfo(req)

        return res.privateKey.decode('utf-8')

    def get_key(self, name: str, public: bool) -> dict:
        req = GetKeyRequest(name=name, public=public)
        res = self.client.GetKey(req)

        if not res.found:
            return None

        return {
            'name': res.key.name,
            'value': res.key.value.decode('utf-8'),
            'public': res.key.public,
            'scheme': res.key.scheme,
        }

    def put_key(self, name: str, value: str, public: bool, scheme: str = "") -> bool:
        key = DiscoveryKey(name=name, value=value.encode('utf-8'), public=public, scheme=scheme)
        req = PutKeyRequest(key=key)
        res = self.client.PutKey(req)

        return {
            'ok': res.ok,
            'error': res.error,
        }

    def list_hospitals(self):
        req = ListRequest()
        res = self.client.ListHospitals(req)

        hospitals = []
        for hospital in res.hospitals:
            public_keys = []
            for key in hospital.publicKeys:
                public_keys.append({
                    'name': key.name,
                    'value': key.value.decode('utf-8'),
                    'scheme': key.scheme,
                })

            hospitals.append({
                'id': hospital.id,
                'name': hospital.name,
                'registered_time': datetime.fromtimestamp(hospital.registeredTime).isoformat(),
                'public_key': hospital.publicKey.decode('utf-8'),
                'gateway_addr': hospital.gatewayAddr,
                'consistent_storage_addr': hospital.consistentStorageAddr,
                'public_keys': public_keys,
            })

        return hospitals

    def find_hospital(self, hospital_id):
        hospitals = self.list_hospitals()
        for hospital in hospitals:
            if hospital['id'] == hospital_id:
                return hospital

        return None
