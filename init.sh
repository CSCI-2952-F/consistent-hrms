#!/bin/sh

mkdnet() {
  if [[ ! $(docker network ls --filter "name=^$1$" --quiet) ]]
  then
    docker network create "$1"
  fi
}

ensure_up() {
  project_name=cs2952f-`echo "$1" | sed 's/docker-compose.\(.*\).yml/\1/'`
  echo Starting "$project_name"...

  docker-compose -p "$project_name" -f "$1" up -d --build
  stopped=$(docker-compose -p "$project_name" -f "$1" ps --services --filter status=stopped)
  if [[ "$stopped" ]]
  then
    echo "ERROR: One or more services could not be started: $(echo $stopped | tr '\n' ',' | sed 's/,$/\n/')"
    echo $stopped | xargs docker-compose -f "$1" logs --tail=50
    exit 1
  fi
}

# Create Docker networks for inter-hospital communication
mkdnet hrms-hospital-sagas
mkdnet hrms-hospital-bigchain
mkdnet hrms-hospital-discovery

# Start common infra with Docker Compose
ensure_up docker-compose.discovery.yml
ensure_up docker-compose.sagas.yml
ensure_up docker-compose.bigchaindb.yml
