#!/bin/sh

PROJECT_DIR=../../
python -m grpc_tools.protoc -I "${PROJECT_DIR}/protos" --go_out=plugins=grpc:. "${PROJECT_DIR}/protos/sagas.proto"
