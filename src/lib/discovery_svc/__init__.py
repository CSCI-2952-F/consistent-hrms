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

    def list_hospitals(self):
        req = ListRequest()
        res = self.client.ListHospitals(req)

        hospitals = []
        for hospital in res.hospitals:
            hospitals.append({
                'id': hospital.id,
                'name': hospital.name,
                'registered_time': datetime.fromtimestamp(hospital.registeredTime).isoformat(),
                'public_key': hospital.publicKey.decode('utf-8'),
                'gateway_addr': hospital.gatewayAddr,
            })

        return hospitals

    def find_hospital(self, hospital_id):
        hospitals = self.list_hospitals()
        for hospital in hospitals:
            if hospital['id'] == hospital_id:
                return hospital

        return None
