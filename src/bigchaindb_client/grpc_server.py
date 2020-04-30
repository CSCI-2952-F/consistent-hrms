import traceback

from lib.consistent_storage.base import BaseStorageBackend
from lib.consistent_storage.pb import consistent_storage_pb2 as pb
from lib.consistent_storage.pb.consistent_storage_pb2_grpc import ConsistentStorageServicer


def catch_exc(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Print exception
            tb = traceback.format_exc()
            print(tb, flush=True)

            # Re-raise it to gRPC
            raise e

    return wrapper


class GrpcProxyServer(ConsistentStorageServicer):
    """
    Consistent storage proxy server that exposes a gRPC interface.
    """
    def __init__(self, backend: BaseStorageBackend):
        self.backend = backend

    @catch_exc
    def Get(self, request, context):
        res = self.backend.get(request.key)

        value = res.get('value')
        if not value:
            value = ''
        value = value.encode('utf-8')

        return pb.GetResponse(
            exists=res.get('exists', False),
            value=value,
            isOwner=res.get('is_owner', False),
            owner=res.get('owner', ''),
        )

    @catch_exc
    def Put(self, request, context):
        res = self.backend.put(request.key, request.value.decode('utf-8'))
        return pb.PutResponse(
            ok=res.get('ok', False),
            owner=res.get('owner', ''),
        )

    @catch_exc
    def Remove(self, request, context):
        res = self.backend.remove(request.key)

        error = res.get('error', '')
        if error == 'Key does not exist':
            error = pb.REMOVE_KEY_ERROR
        elif error == 'Not owner of key':
            error = pb.REMOVE_NOT_OWNER
        else:
            print(error, flush=True)
            error = pb.REMOVE_KEY_ERROR  # Default error, not accurate.

        return pb.RemoveResponse(
            removed=res.get('removed', False),
            errorType=error,
        )

    @catch_exc
    def Transfer(self, request, context):
        res = self.backend.transfer(request.key, request.newOwner)

        error = res.get('error', '')
        if error == 'Key does not exist':
            error = pb.TRANSFER_KEY_ERROR
        elif error == 'Not owner of key':
            error = pb.TRANSFER_NOT_OWNER
        else:
            print(error, flush=True)
            error = pb.TRANSFER_KEY_ERROR  # Default error, not accurate.

        return pb.TransferResponse(
            transferred=res.get('transferred', False),
            errorType=error,
        )
