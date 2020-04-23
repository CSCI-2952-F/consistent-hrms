#!/bin/sh

PROJECT_DIR=../../

protoc -I "${PROJECT_DIR}/protos" --go_out=plugins=grpc:. "${PROJECT_DIR}/protos/sagas.proto" "${PROJECT_DIR}/protos/discovery.proto"
