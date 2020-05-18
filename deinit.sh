#!/bin/sh

set -x

rmdnet() {
  docker network rm $1
}

down() {
  yaml_name=`echo "$1" | sed 's/docker-compose.\(.*\).yml/\1/'`
  project_name="cs2952f-$yaml_name"
  echo Destroying "$project_name"...

  files="-f docker-compose.$yaml_name.yml"
  if [[ -f "docker-compose.$yaml_name.override.yml" ]]; then
    files="$files -f docker-compose.$yaml_name.override.yml"
  fi

  dco="docker-compose -p "$project_name" $files"

  $dco down -v --rmi local --remove-orphans
}

rmdnet hrms-interhospital
rmdnet hrms-hospital-sagas
rmdnet hrms-hospital-bigchain
rmdnet hrms-hospital-centraldb
rmdnet hrms-hospital-discovery
rmdnet hrms-loadtesting

down docker-compose.discovery.yml
down docker-compose.sagas.yml
down docker-compose.bigchain.yml
down docker-compose.centraldb.yml
down docker-compose.loadtesting.yml

