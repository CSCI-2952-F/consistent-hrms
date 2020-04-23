from datetime import datetime

import grpc

from api_gateway.discovery_svc.pb.discovery_pb2 import *
from api_gateway.discovery_svc.pb.discovery_pb2_grpc import HospitalDiscoveryStub


class DiscoveryService:
    def __init__(self, grpc_addr):
        channel = grpc.insecure_channel(grpc_addr)
        self.client = HospitalDiscoveryStub(channel)

    def list_hospitals(self):
        req = ListRequest()
        res = self.client.ListHospitals(req)

        hospitals = []
        for hospital in res.hospitals:
            hospitals.append({
                'id': hospital.id,
                'name': hospital.name,
                'registered_time': datetime.fromtimestamp(hospital.registeredTime).isoformat(),
            })

        return hospitals
