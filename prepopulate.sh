#!/bin/sh

docker exec -it newport-hospital_bigchaindb_client_1 python /usr/src/app/prepopulate.py $@
docker cp newport-hospital_bigchaindb_client_1:/usr/src/app/bigchaindb_client/personal_cards src/bigchaindb_client/
