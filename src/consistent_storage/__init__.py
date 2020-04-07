import os

from nameko.rpc import rpc

from lib.exceptions import KeyExistsError

from consistent_storage.sagas import SagasStorageClient

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

    def __init__(self):
        self.sagas = SagasStorageClient(timeout=10)

        if BACKEND == 'sagas':
            self.client = self.sagas
        elif BACKEND == 'bigchain':
            raise NotImplementedError()
        else:
            raise Exception(f'Invalid consistent storage backend: "{BACKEND}"')

    @rpc
    def healthy(self):
        return True

    @rpc
    def get(self, key):
        return self.client.get(key)

    @rpc
    def put(self, key, value):
        success = self.put(key, value)
        if not success:
            raise KeyExistsError(key)

    @rpc
    def remove(self, key):
        success = self.client.remove(key)
        if not success:
            raise KeyError(key)
