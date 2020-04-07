#!/bin/sh

mkdnet() {
  if [[ ! $(docker network ls --filter "name=^$1$" --quiet) ]]
  then
    docker network create "$1"
  fi
}

ensure_up() {
  docker-compose -f "$1" up -d --build
  stopped=$(docker-compose -f "$1" ps --services --filter status=stopped)
  if [[ "$stopped" ]]
  then
    echo "ERROR: One or more services could not be started: $(echo $stopped | tr '\n' ',' | sed 's/,$/\n/')"
    echo $stopped | xargs docker-compose -f "$1" logs --tail=50
    exit 1
  fi
}

# Create Docker network for 2PC and BigchainDB clients
mkdnet hrms-hospital-sagas
mkdnet hrms-hospital-bigchain

# Start sagas
ensure_up docker-compose.sagas.yml
