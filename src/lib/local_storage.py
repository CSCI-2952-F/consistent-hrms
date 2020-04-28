import os

from redis import Redis

from lib import crypto


class LocalStorage():
    def __init__(self):
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = int(os.environ.get('REDIS_PORT', '6379'))

        # Returned responses are always decoded into strings
        self.redis = Redis(host=redis_host, port=redis_port, decode_responses=True)

    def delete_key(self, uid):
        """
        Removes a key from local storage.
        If the key refers to a list (patient records), all records are deleted.
        Returns the total number of items deleted.
        """

        return self.redis.delete(uid)

    def insert_item(self, uid, public_key, value):
        """
        Inserts a new item into a list in local storage with encrypted data.
        """

        value = crypto.encrypt(str(value), public_key)
        self.redis.rpush(uid, value)

    def load_items(self, uid, items):
        """
        Loads items directly into local storage.
        """

        self.redis.rpush(uid, *items)

    def get_items(self, uid, offset=0, length=None):
        """
        Retrieves encrypted items from a list in local storage,
        optionally with offset and length parameters.
        """

        if length is None:
            length = -1

        return self.redis.lrange(uid, offset, length)

    def add_staff(self, physician_id, value):
        """
        Update hospital staff roster.
        """

        self.redis.rpush(physician_id, value)

    def valid_staff(self, physician_id):
        """
        Return True if physician_id exists in staff roster.
        """

        return self.redis.exists(physician_id)
