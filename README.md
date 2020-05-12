# Consistent Storage Between Mutual Distrustful Parties

## Instructions

### Starting up

First, run `init.sh`, which will bootstrap any necessary dependencies. This only needs to be done once, or whenever the script itself is changed.

> NOTE: You need to restart the **tendermint** container by calling `docker restart cs2952f-bigchain_tendermint_1`

A useful Python script has been included to start various hospital namespaces, orchestrated using Docker Compose. The number of namespaces started depends on the list of hospital names in `data/hospitals.txt`.

To start all hospitals, run:

```sh
python hospitals.py start
```

> _NOTE: If this is your first time running the system_ OR _you have just rebuilt the bigchaindb service_

You need to seed bigchaindb with unregistered patient assets. Run the following commands:

```sh
./prepopulate.sh 1 alice
./prepopulate.sh 1 bob
./prepopulate.sh 1 charlie
```

The patient cards will be found in `src/bigchaindb_client/patient_cards/`.

If you would like to reseed bigchain, do this:

```sh
docker-compose -f docker-compose.bigchain.yml -p cs2952f-bigchain down -v
docker-compose -f docker-compose.bigchain.yml -p cs2952f-bigchain up -d --build
```

The frontend servers will be listening on the local interface, at ports starting from 8000.

### Development

When making source code changes, it is necessary to rebuild the services. You can use `python hospitals.py start` to rebuild and reload just the changed services.

The `hospitals.py` script also provides useful aliases for working with multiple Docker Compose projects. For example, to view the running containers across all hospitals, you can use:

```sh
$ python hospitals.py ps
[*] Executing: /usr/local/bin/docker-compose -f docker-compose.hospital.yml -p rhode-island-hospital ps
                   Name                                 Command                  State                        Ports
------------------------------------------------------------------------------------------------------------------------------------
rhode-island-hospital_api_gateway_1          bash -c nameko run ${MODUL ...   Up (healthy)   127.0.0.1:8100->80/tcp
rhode-island-hospital_consistent_storage_1   nameko run consistent_stor ...   Up
rhode-island-hospital_frontend_1             python main.py                   Up             127.0.0.1:8000->80/tcp
rhode-island-hospital_patient_service_1      bash -c nameko run ${MODUL ...   Up
rhode-island-hospital_physician_service_1    bash -c nameko run ${MODUL ...   Up
rhode-island-hospital_rabbitmq_1             docker-entrypoint.sh rabbi ...   Up             25672/tcp, 4369/tcp, 5671/tcp, 5672/tcp
rhode-island-hospital_redis_1                docker-entrypoint.sh redis ...   Up             6379/tcp
rhode-island-hospital_sagas_1                sagas                            Up             8080/tcp
[*] Executing: /usr/local/bin/docker-compose -f docker-compose.hospital.yml -p miriam-hospital ps
                Name                              Command                  State                        Ports
------------------------------------------------------------------------------------------------------------------------------
miriam-hospital_api_gateway_1          bash -c nameko run ${MODUL ...   Up (healthy)   127.0.0.1:8101->80/tcp
miriam-hospital_consistent_storage_1   nameko run consistent_stor ...   Up
miriam-hospital_frontend_1             python main.py                   Up             127.0.0.1:8001->80/tcp
miriam-hospital_patient_service_1      bash -c nameko run ${MODUL ...   Up
miriam-hospital_physician_service_1    bash -c nameko run ${MODUL ...   Up
miriam-hospital_rabbitmq_1             docker-entrypoint.sh rabbi ...   Up             25672/tcp, 4369/tcp, 5671/tcp, 5672/tcp
miriam-hospital_redis_1                docker-entrypoint.sh redis ...   Up             6379/tcp
miriam-hospital_sagas_1                sagas                            Up             8080/tcp
[*] Executing: /usr/local/bin/docker-compose -f docker-compose.hospital.yml -p newport-hospital ps
                Name                               Command                  State                        Ports
-------------------------------------------------------------------------------------------------------------------------------
newport-hospital_api_gateway_1          bash -c nameko run ${MODUL ...   Up (healthy)   127.0.0.1:8102->80/tcp
newport-hospital_consistent_storage_1   nameko run consistent_stor ...   Up
newport-hospital_frontend_1             python main.py                   Up             127.0.0.1:8002->80/tcp
newport-hospital_patient_service_1      bash -c nameko run ${MODUL ...   Up
newport-hospital_physician_service_1    bash -c nameko run ${MODUL ...   Up
newport-hospital_rabbitmq_1             docker-entrypoint.sh rabbi ...   Up             25672/tcp, 4369/tcp, 5671/tcp, 5672/tcp
newport-hospital_redis_1                docker-entrypoint.sh redis ...   Up             6379/tcp
newport-hospital_sagas_1                sagas                            Up             8080/tcp
```

The list of proxied commands to Docker Compose can be found in `hospitals.py`.

To view Docker Compose information for a single hospital, use the following command syntax:

```sh
docker-compose -f docker-compose.hospital.yml -p <HOSPITAL-NAME> <COMMAND>
```

For example, to view all containers for Rhode Island Hospital, do the following:

```sh
docker-compose -f docker-compose.hospital.yml -p rhode-island-hospital ps
```

### Tearing down

To terminate all containers, use the helper script again:

```sh
python hospitals.py stop
```

If you want to permanently

## Configuration

You can specify various configuration for running different types of experiments on the architecture.

The following environment variables are used:

- `CONSISTENT_STORAGE_BACKEND`: Choose the backend used for consistent storage. Options: `sagas`, `bigchain`
- `SAGAS_NUM_PARTITIONS`: Number of partitions in the Kafka topic, to increase parallelism.
  - When changing this, Kafka will probably complain. It's best to delete the topic whenever you need to change the number of partitions in order to run experiments.

You can also choose to spin up more hospitals by adding or removing lines in `data/hospitals.txt`.

## Style Guide

### General

Use [EditorConfig](https://editorconfig.org/) to configure your IDE to respect the configuration file located in `.editorconfig`.

### Prettier

This project uses [Prettier](https://prettier.io/) to format JS, HTML, CSS and Markdown files automatically. The configuration is located in `.prettierrc`.

### Python

This project uses [Pylint](https://www.pylint.org/) and [YAPF](https://github.com/google/yapf) for linting and code formatting respectively. Configure your IDE to use the configuration files `.pylintrc` and `style.cfg` respectively.

### Go

This project uses [`go fmt`](https://golang.org/pkg/fmt/) for formatting Go code, without any custom configuration.
