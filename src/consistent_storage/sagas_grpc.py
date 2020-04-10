import os

import grpc

from consistent_storage.sagas_pb2 import *
from consistent_storage.sagas_pb2_grpc import SagasConsistentStorageStub

GRPC_ADDR = os.getenv('SAGAS_GRPC_ADDR')
if not GRPC_ADDR:
    raise Exception('SAGAS_GRPC_ADDR not set')


class SagasGrpcClient:
    def __init__(self):
        channel = grpc.insecure_channel(GRPC_ADDR)
        self.client = SagasConsistentStorageStub(channel)

    def get(self, key):
        raise NotImplementedError()

    def put(self, key: str, value: str) -> bool:
        req = PutRequest(key=key, value=value.encode('utf-8'))
        res = self.client.Put(req)
        return res.ok

    def remove(self, key) -> bool:
        raise NotImplementedError()
