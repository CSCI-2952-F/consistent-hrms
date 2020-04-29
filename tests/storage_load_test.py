"""
Load test for consistent storage operations.
"""

import random
import re
import string
import sys
import time

import grequests

from keys import PUBLIC_KEY


def random_key():
    # Returns a random 32 byte key.
    # This is the same length as a SHA256 hash.
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(32))


def dispatch(method, get_data, ports):
    """
    Dispatch requests asynchronously and return the time taken, as well as the results.

    Arguments:
        method {str} -- Method name.
        get_data {Generator[Dict, None, None]} -- Generator that yields JSON data. Determines total number of requests.
                                                  The same data will be used for all ports per request.
        ports {List[int]} -- List of port numbers that the requests should dispatch to.
    """

    reqs = (grequests.request(method, f'http://localhost:{port}/', json=data) for port in ports for data in get_data)

    responses = grequests.map(reqs)
    total_duration = sum([res.elapsed.total_seconds() for res in responses])

    return total_duration, responses


def run(test, num_requests, hospitals):
    slugs = (re.sub('[^a-z]+', '-', name.lower()) for name in hospitals)
    num_hospitals = len(hospitals)

    # Ports refer to consistent storage HTTP server.
    ports = range(8200, 8200 + num_hospitals)

    if test == "get":
        # Fetch random, non-existent keys
        data = ({'key': random_key()} for _ in range(num_requests))
        duration, responses = dispatch('GET', data, ports)

        # Count successes
        num_success = len([1 for res in responses if res.json()['exists']])
        return duration, num_success

    elif test == "get_existing":
        # Generate random keys
        keys = [random_key() for _ in range(num_requests)]

        # Put random keys
        data = ({'key': key, 'value': PUBLIC_KEY} for key in keys)
        dispatch('PUT', data, ports)

        # Now measure getting the keys
        data = ({'key': key} for key in keys)
        duration, responses = dispatch('GET', data, ports)

        # Count successes
        num_success = len([1 for res in responses if res.json()['exists']])
        return duration, num_success

    elif test == "put":
        # Put random keys
        data = ({'key': random_key(), 'value': PUBLIC_KEY} for _ in range(num_requests))
        duration, responses = dispatch('PUT', data, ports)

        # Count successes
        num_success = len([1 for res in responses if res.json()['ok']])
        return duration, num_success

    elif test == "remove":
        # Generate random keys
        keys = [random_key() for _ in range(num_requests)]

        # Put keys initially
        data = ({'key': key, 'value': PUBLIC_KEY} for key in keys)
        dispatch('PUT', data, ports)

        # Now measure the removal
        data = ({'key': key} for key in keys)
        duration, responses = dispatch('REMOVE', data, ports)

        # Count successes
        num_success = len([1 for res in responses if res.json()['removed']])
        return duration, num_success

    elif test == "transfer":
        # Generate random keys
        keys = [random_key() for _ in range(num_requests)]

        # Put keys initially
        data = ({'key': key, 'value': PUBLIC_KEY} for key in keys)
        dispatch('PUT', data, ports)

        # Now transfer them all to some random hospital
        owners = (random.choice(slugs) for _ in range(num_requests))
        data = ({'key': key, 'owner': owner} for key, owner in zip(keys, owners))
        duration, responses = dispatch('TRANSFER', data, ports)

        # Count successes
        num_success = len([1 for res in responses if res.json()['transferred']])
        return duration, num_success

    else:
        raise Exception('Unknown test:', test)


def main():
    if len(sys.argv) != 3:
        print('Usage python storage_load_test.py <test> <num_requests>')
        sys.exit(1)

    test = sys.argv[1].strip().lower()
    num_requests = int(sys.argv[2])

    # Read hospitals
    with open('data/hospitals.txt') as f:
        hospitals = [line.strip() for line in f.readlines() if line.strip()]

    # Dispatch requests
    duration, successes = run(test, num_requests, hospitals)

    print(f'Total duration: {duration:.4f}s for {num_requests} requests each at {len(hospitals)} hospitals')
    print(f'Number of successes: {successes}')
    avg_time = duration / num_requests
    print(f'Average time per request: {avg_time:.6f}s')


if __name__ == "__main__":
    main()
