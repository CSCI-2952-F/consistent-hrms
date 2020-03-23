import json

from nameko.rpc import rpc


class PhysicianService:
    name = 'physician_service'

    @rpc
    def healthy(self):
        """
        Returns True if service is healthy.
        """
        return True
