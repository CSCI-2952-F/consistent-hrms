import base64
import os

import grpc

from consistent_storage.sagas.pb.sagas_pb2 import *
from consistent_storage.sagas.pb.sagas_pb2_grpc import SagasConsistentStorageStub
from lib.consistent_storage import BaseStorageBackend


class SagasBackend(BaseStorageBackend):
    """
    Basic client to proxy requests from the consistent_storage Nameko server
    to the underlying sagas gRPC server.

    Implements the BaseStorageBackend interface.
    """
    def __init__(self, grpc_addr):
        channel = grpc.insecure_channel(grpc_addr)
        self.client = SagasConsistentStorageStub(channel)

    def get(self, key: str) -> dict:
        req = GetRequest(key=key)
        res = self.client.Get(req)

        if not res.exists:
            return {
                'exists': False,
                'value': None,
            }

        return {
            'exists': True,
            'value': res.value.decode('utf-8'),
            'is_owner': res.isOwner,
            'owner': res.owner,
        }

    def put(self, key: str, value: str) -> dict:
        req = PutRequest(key=key, value=value.encode('utf-8'))
        res = self.client.Put(req)

        return {
            'ok': res.ok,
            'owner': res.owner,
        }

    def remove(self, key: str) -> dict:
        req = RemoveRequest(key=key)
        res = self.client.Remove(req)
        if res.removed:
            return {
                'removed': True,
            }

        if res.errorType == REMOVE_KEY_ERROR:
            error = 'Key does not exist'
        elif res.errorType == REMOVE_NOT_OWNER:
            error = 'Not owner of key'

        return {
            'removed': False,
            'error': error,
        }

    def transfer(self, key: str, dest: str) -> dict:
        req = TransferRequest(key=key, newOwner=dest)
        res = self.client.Transfer(req)
        if res.transferred:
            return {
                'transferred': True,
            }

        if res.errorType == TRANSFER_KEY_ERROR:
            error = 'Key does not exist'
        elif res.errorType == TRANSFER_NOT_OWNER:
            error = 'Not owner of key'

        return {
            'transferred': False,
            'error': error,
        }
