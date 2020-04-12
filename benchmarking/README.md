# Benchmarking Tools

## Instructions

These tools require Python 3.7, and dependencies that can be installed from `requirements.txt`. In a virtual environment, run:

```sh
pip install -r requirements.txt
```

Make sure all the necessary containers are already set up and running.

## Consistent Storage Load Test

A Python script `consistent_storage_load_test.py` allows you to run a load test on consistent storage by hammering the patient registration endpoint with concurrent registrations for the same patient across multiple hospitals.

In a setting where linearizability is necessitated, running concurrent requests in a large pool of hospitals might be slow. As such, we can use this script to test the runtime when using different backends, as well as the correctness by running lots of conflicting requests at the same time.

The script uses [grequests](https://github.com/spyoungtech/grequests) (using [gevent](http://www.gevent.org/) under the hood) to run each HTTP requests in an asynchronous manner; this prevents the load testing tool from being the bottleneck itself.
