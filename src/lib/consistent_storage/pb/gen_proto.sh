#!/bin/sh

PROJECT_DIR=../../../../
python -m grpc_tools.protoc -I "${PROJECT_DIR}/protos" --python_out=. --grpc_python_out=. "${PROJECT_DIR}/protos/consistent_storage.proto"
2to3 -wn -f import *.py
