# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from . import sagas_pb2 as sagas__pb2


class SagasConsistentStorageStub(object):
    """Missing associated documentation comment in .proto file"""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Get = channel.unary_unary(
                '/SagasConsistentStorage/Get',
                request_serializer=sagas__pb2.GetRequest.SerializeToString,
                response_deserializer=sagas__pb2.GetResponse.FromString,
                )
        self.Put = channel.unary_unary(
                '/SagasConsistentStorage/Put',
                request_serializer=sagas__pb2.PutRequest.SerializeToString,
                response_deserializer=sagas__pb2.PutResponse.FromString,
                )
        self.Remove = channel.unary_unary(
                '/SagasConsistentStorage/Remove',
                request_serializer=sagas__pb2.RemoveRequest.SerializeToString,
                response_deserializer=sagas__pb2.RemoveResponse.FromString,
                )


class SagasConsistentStorageServicer(object):
    """Missing associated documentation comment in .proto file"""

    def Get(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Put(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Remove(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_SagasConsistentStorageServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Get': grpc.unary_unary_rpc_method_handler(
                    servicer.Get,
                    request_deserializer=sagas__pb2.GetRequest.FromString,
                    response_serializer=sagas__pb2.GetResponse.SerializeToString,
            ),
            'Put': grpc.unary_unary_rpc_method_handler(
                    servicer.Put,
                    request_deserializer=sagas__pb2.PutRequest.FromString,
                    response_serializer=sagas__pb2.PutResponse.SerializeToString,
            ),
            'Remove': grpc.unary_unary_rpc_method_handler(
                    servicer.Remove,
                    request_deserializer=sagas__pb2.RemoveRequest.FromString,
                    response_serializer=sagas__pb2.RemoveResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'SagasConsistentStorage', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class SagasConsistentStorage(object):
    """Missing associated documentation comment in .proto file"""

    @staticmethod
    def Get(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/SagasConsistentStorage/Get',
            sagas__pb2.GetRequest.SerializeToString,
            sagas__pb2.GetResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Put(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/SagasConsistentStorage/Put',
            sagas__pb2.PutRequest.SerializeToString,
            sagas__pb2.PutResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Remove(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/SagasConsistentStorage/Remove',
            sagas__pb2.RemoveRequest.SerializeToString,
            sagas__pb2.RemoveResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)