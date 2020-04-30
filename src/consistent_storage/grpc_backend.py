import grpc

from lib.consistent_storage.base import BaseStorageBackend
from lib.consistent_storage.pb.consistent_storage_pb2 import *
from lib.consistent_storage.pb.consistent_storage_pb2_grpc import ConsistentStorageStub


class GrpcStorageBackend(BaseStorageBackend):
    """
    Basic client to proxy requests from the consistent_storage Nameko server
    to the underlying gRPC server that fulfils consistent storage guarantees.

    Implements the BaseStorageBackend interface.
    """
    def __init__(self, grpc_addr):
        self.channel = grpc.insecure_channel(grpc_addr)
        self.client = ConsistentStorageStub(self.channel)

    def get(self, key: str) -> dict:
        req = self._get_request(key)
        res = self.client.Get(req)
        return self._handle_get_response(res)

    def _get_request(self, key: str) -> GetRequest:
        return GetRequest(key=key)

    def _handle_get_response(self, res: GetResponse) -> dict:
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
        req = self._put_request(key, value)
        res = self.client.Put(req)
        return self._handle_put_response(res)

    def _put_request(self, key: str, value: str) -> PutRequest:
        return PutRequest(key=key, value=value.encode('utf-8'))

    def _handle_put_response(self, res: PutResponse) -> dict:
        return {
            'ok': res.ok,
            'owner': res.owner,
        }

    def remove(self, key: str) -> dict:
        req = self._remove_request(key)
        res = self.client.Remove(req)
        return self._handle_remove_response(res)

    def _remove_request(self, key: str) -> RemoveRequest:
        return RemoveRequest(key=key)

    def _handle_remove_response(self, res: RemoveResponse) -> dict:
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
        req = self._transfer_request(key, dest)
        res = self.client.Transfer(req)
        return self._handle_transfer_response(res)

    def _transfer_request(self, key: str, dest: str) -> TransferRequest:
        return TransferRequest(key=key, newOwner=dest)

    def _handle_transfer_response(self, res: TransferResponse) -> dict:
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
