import grpc
import rsa

from consistent_storage.pb.consistent_storage_pb2 import *
from consistent_storage.pb.consistent_storage_pb2_grpc import CentralConsistentStorageStub
from consistent_storage.grpc_backend import GrpcStorageBackend
from lib import crypto
from lib.discovery_svc import DiscoveryService


class CentralDBStorageBackend(GrpcStorageBackend):
    """
    This storage backend wraps requests and sends them to a CentralDB gRPC server.
    """
    def __init__(self, grpc_addr):
        super().__init__(grpc_addr)

        # Use DiscoveryService to get our metadata
        self.discovery_svc = DiscoveryService()
        self.hospital_id = self.discovery_svc.get_id()
        self.priv_key = self.discovery_svc.get_private_key()

        # Create gRPC client to CentralDB server instead
        self.client = CentralConsistentStorageStub(self.channel)

    def get(self, key: str) -> dict:
        req = self._get_request(key)
        res = self._wrap('get', req)
        return self._handle_get_response(res)

    def put(self, key: str, value: str) -> dict:
        req = self._put_request(key, value)
        res = self._wrap('put', req)
        return self._handle_put_response(res)

    def remove(self, key: str) -> dict:
        req = self._remove_request(key)
        res = self._wrap('remove', req)
        return self._handle_remove_response(res)

    def transfer(self, key: str, dest: str) -> dict:
        req = self._transfer_request(key, dest)
        res = self._wrap('transfer', req)
        return self._handle_transfer_response(res)

    def _wrap(self, key, req):
        # Sign request
        signature = crypto.sign(req.SerializeToString(), crypto.load_privkey(self.priv_key))

        # Prepare WrappedRequest
        kwargs = {
            'id': self.hospital_id,
            'signature': signature,
            key: req,
        }
        req = WrappedRequest(**kwargs)

        # Send request
        res = self.client.Request(req)

        # Unwrap response
        assert res.HasField(key)
        return getattr(res, key)
