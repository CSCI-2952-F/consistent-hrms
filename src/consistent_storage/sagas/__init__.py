"""
Our implementation of the Sagas design pattern using Apache Kafka as the shared message bus.
This contains the library code for interacting with Kafka and exposes a KV-store API for
ConsistentStorageProxy can proxy incoming requests to.
"""


class SagasStorage:
    def get(self, key):
        raise NotImplementedError()

    def put(self, key, value):
        raise NotImplementedError()

    def remove(self, key):
        raise NotImplementedError()
