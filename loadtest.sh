#!/bin/sh

LOADTESTER="$1"

case "$LOADTESTER" in

"golang")
  docker exec -it cs2952f-loadtesting_loadtester_1 ./loadtester ${@:2}
  ;;

"python")
  docker exec -it cs2952f-loadtesting_loadtester-py_1 python -m loadtesting_py.test_storage ${@:2}
  ;;

*)
  echo 'Usage: ./loadtest.sh [golang|python] [arguments]'
  exit 1
  ;;

esac
