# Consistent Storage Between Mutual Distrustful Parties

## Instructions

A useful Python script has been included to start various hospital namespaces, orchestrated using Docker Compose. The number of namespaces started depends on the list of hospital names in `data/hospitals.txt`.

To start all hospitals, run:

```sh
python start_hospitals.py
```

The frontend servers will be listening on the local interface, at ports starting from 8000.

To view Docker Compose information for a single hospital, use the following command syntax:

```sh
docker-compose -f docker-compose.hospital.yml -p <HOSPITAL-NAME> <COMMAND>
```

For example, to view all containers for Rhode Island Hospital, do the following:

```sh
docker-compose -f docker-compose.hospital.yml -p rhode-island-hospital ps
```
