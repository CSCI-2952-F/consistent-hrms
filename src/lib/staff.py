import os

from redis import Redis

class Staff():
    def __init__(self):
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = int(os.environ.get('REDIS_PORT', '6379'))
        self.redis = Redis(host=redis_host, port=redis_port)

    def add(self, physician_id, value):
        """
        Update hospital staff roster.
        """

        raise NotImplementedError()

    def valid(self, physician_id):
        """
        Return True if physician_id exists in staff roster.
        """

        raise NotImplementedError()
    
    def staff(self):
        """
        Return hospital staff roster.
        """

        raise NotImplementedError()