# Consistent Storage Between Mutual Distrustful Parties

## Instructions

A useful Python script has been included to start various hospital namespaces, orchestrated using Docker Compose. The number of namespaces started depends on the list of hospital names in `data/hospitals.txt`.

To start all hospitals, run:

```sh
python hospitals.py start
```

The frontend servers will be listening on the local interface, at ports starting from 8000. 

When running the frontend service install the [moesif CORS extension](https://chrome.google.com/webstore/detail/moesif-orign-cors-changer/digfbfaphojjndkpccljibejjbppifbc/related?hl=en-US). The extension will override the CORS header that the server has in place with a wildcard value so that our frontend service can access the api gateway on a different port. 

(We can alternatively look into adding [nameko-cors](https://github.com/harel/nameko-cors))

To view Docker Compose information for a single hospital, use the following command syntax:

```sh
docker-compose -f docker-compose.hospital.yml -p <HOSPITAL-NAME> <COMMAND>
```

For example, to view all containers for Rhode Island Hospital, do the following:

```sh
docker-compose -f docker-compose.hospital.yml -p rhode-island-hospital ps
```

To terminate all containers, use the helper script again:

```sh
python hospitals.py stop
```

## Configuration

You can specify various configuration for running different types of experiments on the architecture.

The following environment variables are used:

- `CONSISTENT_STORAGE_BACKEND`: Choose the backend used for consistent storage. Options: `sagas`, `bigchain`
- `SAGAS_NUM_PARTITIONS`: Number of partitions in the Kafka topic, to increase parallelism.
  - When changing this, Kafka will probably complain. It's best to delete the topic whenever you need to change the number of partitions in order to run experiments.

You can also choose to spin up more hospitals by adding or removing lines in `data/hospitals.txt`.
