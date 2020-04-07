import asyncio

from consistent_storage.sagas.storage import SagasStorage


class SagasStorageClient:
    def __init__(self, timeout=10):
        self._loop = asyncio.get_event_loop()
        self.timeout = timeout
        self.sagas = SagasStorage(loop=self._loop)

    def get(self, key):
        raise NotImplementedError()

    def put(self, key, value):
        coro = asyncio.wait_for(self.sagas.put(key, value), timeout=self.timeout, loop=self._loop)
        self._loop.run_until_complete(coro)
        return coro.result()

    def remove(self, key):
        raise NotImplementedError()
