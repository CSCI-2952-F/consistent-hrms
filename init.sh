#!/bin/sh

mkdnet() {
  if [[ ! $(docker network ls --filter "name=^$1$" --quiet) ]]
  then
    docker network create "$1"
  fi
}

# Create Docker network for 2PC and BigchainDB clients
mkdnet hrms-hospital-2pc
mkdnet hrms-hospital-bigchain
