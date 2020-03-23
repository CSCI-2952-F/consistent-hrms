from nameko.rpc import rpc


class ConsistentStorageProxy:
    """
    Proxy for consistent storage based on the chosen backend.
    Exposes a simple key-value store interface via RPC.
    The storage semantics is that only one client should be able
    to put a given key; all others should fail subsequently until
    the key is removed from the consistent storage.
    """

    name = 'consistent_storage'

    @rpc
    def healthy(self):
        return True

    @rpc
    def get(self, key):
        raise NotImplementedError()

    @rpc
    def put(self, key, value):
        raise NotImplementedError()

    @rpc
    def remove(self, key):
        raise NotImplementedError()
