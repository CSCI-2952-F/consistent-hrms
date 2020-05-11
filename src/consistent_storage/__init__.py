import json
import os

from nameko.rpc import rpc
from nameko.web.handlers import http
from nameko_prometheus import PrometheusMetrics

from consistent_storage.centraldb import CentralDBStorageBackend
from consistent_storage.sagas import SagasBackend
from consistent_storage.bigchain import BigchaindbBackend
from lib.consistent_storage.base import BaseStorageBackend

BACKEND = os.getenv('CONSISTENT_STORAGE_BACKEND', 'sagas')


class ConsistentStorageProxy:
    """
    Proxy for consistent storage based on the chosen backend.
    Exposes a simple key-value store interface via RPC.
    The storage semantics is that only one client should be able
    to put a given key; all others should fail subsequently until
    the key is removed from the consistent storage.
    """

    name = 'consistent_storage'
    metrics = PrometheusMetrics()

    def __init__(self):
        self.backend = BaseStorageBackend()

        if BACKEND == 'sagas':
            grpc_addr = os.getenv('SAGAS_GRPC_ADDR')
            if not grpc_addr:
                raise Exception('SAGAS_GRPC_ADDR not set')

            self.backend = SagasBackend(grpc_addr)

        elif BACKEND == 'bigchain':
            grpc_addr = os.getenv('BIGCHAIN_GRPC_ADDR')
            if not grpc_addr:
                raise Exception('BIGCHAIN_GRPC_ADDR not set')

            self.backend = BigchaindbBackend(grpc_addr)

        elif BACKEND == 'centraldb':
            grpc_addr = os.getenv('CENTRALDB_GRPC_ADDR')
            if not grpc_addr:
                raise Exception('CENTRALDB_GRPC_ADDR not set')

            self.backend = CentralDBStorageBackend(grpc_addr)

        else:
            raise Exception(f'Invalid consistent storage backend: "{BACKEND}"')

    @rpc
    def healthy(self):
        return True

    @rpc
    def get(self, key: str) -> dict:
        """
        Fetches a key from consistent storage.

        Arguments:
            key {str} -- Key to fetch. Patient's UUIF

        Returns:
            dict --  Returns a dictionary as follows:

            {
                'exists': [bool],
                'value': [str or NoneType],  # Patient's public key
                'is_owner': [bool],
                'owner': [str],
            }

            If the key does not exist, the `is_owner` and `owner`
            metadata keys may not be present in the returned dictionary.
        """
        return self.backend.get(key)

    @rpc
    def put(self, key: str, value: str) -> dict:
        """
        Stores a key in the consistent storage in an atomic, linearizable fashion.
        Fails if the key is already present and stored by another owner.

        Arguments:
            key {str} -- Key to store. Patient's UUID
            value {str} -- Value to store. Patients's public key

        Returns:
            dict --  Returns a dictionary as follows:

            {
                'ok': [bool],
                'owner': [str],
            }
        """
        if BACKEND == 'bigchain':
            return self.backend.transfer_to_register(key, value)
        else:
            return self.backend.put(key, value)

    @rpc
    def remove(self, key: str) -> dict:
        """
        Removes a key in the consistent storage in an atomic, linearizable fashion.
        Fails if the key is not in storage, or is owned by another owner.

        Arguments:
            key {str} -- Key to remove.

        Returns:
            dict --  Returns a dictionary as follows:

            {
                'removed': [bool],
                'error': [str],
            }
        """
        return self.backend.remove(key)

    @rpc
    def transfer(self, key: str, dest: str) -> dict:
        """
        Transfer a key in the consistent storage to a new owner in an atomic, linearizable fashion.
        Fails if the key is not in storage, or is owned by another owner.

        Arguments:
            key {str} -- Key to remove.
            dest {str} -- Destination hospital name.

        Returns:
            dict --  Returns a dictionary as follows:

            {
                'transferred': [bool],
                'error': [str],
            }
        """
        return self.backend.transfer(key, dest)

    @http('GET', '/')
    def http_get(self, request):
        return self._handle_http(self.get, request)

    @http('PUT', '/')
    def http_put(self, request):
        return self._handle_http(self.put, request)

    @http('REMOVE', '/')
    def http_remove(self, request):
        return self._handle_http(self.remove, request)

    @http('TRANSFER', '/')
    def http_transfer(self, request):
        return self._handle_http(self.transfer, request)

    def _handle_http(self, handler, request):
        data = json.loads(request.get_data(as_text=True))
        res = handler(**data)
        return json.dumps(res)

    @http('GET', '/metrics')
    def serve_metrics(self, request):
        return self.metrics.expose_metrics(request)
