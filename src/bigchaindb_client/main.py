import os
import time
from concurrent import futures

import grpc
from lib.consistent_storage.pb.consistent_storage_pb2_grpc import add_ConsistentStorageServicer_to_server
from bigchaindb_client.grpc_server import GrpcProxyServer
from bigchaindb_client.bigchain_backend import BigchaindbBackend

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def serve():
    bdb_root_url = os.getenv('BIGCHAIN_ROOT_URL')
    if not bdb_root_url:
        raise Exception('BIGCHAIN_ROOT_URL not set')

    listen_addr = os.getenv('GRPC_LISTEN_ADDR')
    if not listen_addr:
        raise Exception('GRPC_LISTEN_ADDR not set')

    # Initialize Bigchaindb backend, and a gRPC server in front of it
    backend = BigchaindbBackend(bdb_root_url)
    servicer = GrpcProxyServer(backend)

    # Start gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_ConsistentStorageServicer_to_server(servicer, server)
    server.add_insecure_port(listen_addr)
    server.start()

    # Sleep loop to keep gRPC server alive
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
