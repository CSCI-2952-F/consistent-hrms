import base64
import os

import grpc

from consistent_storage.base import BaseClient
from consistent_storage.sagas_pb2 import *
from consistent_storage.sagas_pb2_grpc import SagasConsistentStorageStub

GRPC_ADDR = os.getenv('SAGAS_GRPC_ADDR')
if not GRPC_ADDR:
    raise Exception('SAGAS_GRPC_ADDR not set')


class SagasGrpcClient(BaseClient):
    def __init__(self):
        channel = grpc.insecure_channel(GRPC_ADDR)
        self.client = SagasConsistentStorageStub(channel)

    def get(self, key: str) -> dict:
        req = GetRequest(key=key)
        res = self.client.Get(req)
        if not res.exists:
            return {
                'value': None,
            }
        
        return {
            'value': base64.b64encode(res.value).decode('utf-8'),
            'is_owner': res.isOwner,
            'owner': res.owner,
        }

    def put(self, key: str, value: bytes) -> bool:
        req = PutRequest(key=key, value=value)
        res = self.client.Put(req)
        return res.ok

    def remove(self, key: str) -> bool:
        req = RemoveRequest(key=key)
        res = self.client.Remove(req)
        return res.removed
