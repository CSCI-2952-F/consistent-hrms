"""
Persistent storage for Kafka-based Sagas implementation.
This is the local replicated log that should be linearizable with respect
to all other Sagas clients.
"""


class BasePersistentSagasStorage:
    def retrieve(self, key):
        data = self._get(key)
        if data is None:
            return None, {}
        return data['value'], data['meta']

    def store(self, key, value, offset, owner):
        self._set(key, {
            'meta': {
                'offset': offset,
                'owner': owner,
            },
            'value': value,
        })

    def remove(self, key, offset, owner):
        self.store(key, None, offset, owner)

    def _get(self, key):
        raise NotImplementedError()

    def _set(self, key, value):
        raise NotImplementedError()
