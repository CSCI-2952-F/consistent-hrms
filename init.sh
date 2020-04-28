#!/bin/sh

mkdnet() {
  if [[ ! $(docker network ls --filter "name=^$1$" --quiet) ]]
  then
    docker network create "$1"
  fi
}

ensure_up() {
  yaml_name=`echo "$1" | sed 's/docker-compose.\(.*\).yml/\1/'`
  project_name="cs2952f-$yaml_name"
  echo Starting "$project_name"...

  files="-f docker-compose.$yaml_name.yml"
  if [[ -f "docker-compose.$yaml_name.override.yml" ]]; then
    files="$files -f docker-compose.$yaml_name.override.yml"
  fi

  dco="docker-compose -p "$project_name" $files"

  $dco up -d --build
  stopped=$($dco ps --services --filter status=stopped)
  if [[ "$stopped" ]]
  then
    echo "ERROR: One or more services could not be started: $(echo $stopped | tr '\n' ',' | sed 's/,$/\n/')"
    echo $stopped | xargs $dco logs --tail=50
    exit 1
  fi
}

# Create Docker networks for inter-hospital communication
mkdnet hrms-interhospital
mkdnet hrms-hospital-sagas
mkdnet hrms-hospital-bigchain
mkdnet hrms-hospital-centraldb
mkdnet hrms-hospital-discovery

# Start common infra with Docker Compose
ensure_up docker-compose.discovery.yml
ensure_up docker-compose.sagas.yml
ensure_up docker-compose.centraldb.yml
