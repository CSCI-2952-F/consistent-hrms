# Consistent Storage Between Mutual Distrustful Parties

## Instructions

A useful Python script has been included to start various hospital namespaces, orchestrated using Docker Compose. The number of namespaces started depends on the list of hospital names in `data/hospitals.txt`.

To start all hospitals, run:

```sh
python start_hospitals.py
```

The frontend servers will be listening on the local interface, at ports starting from 8000.
