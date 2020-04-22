"""
End-to-end test for registering a patient on hospital A, unregistering on hospital A,
followed by registering the patient on hospital B.

Requires at least 2 hospitals to be running. Assumes their API gateways are accessible at
ports 8100 and 8101 respectively.
"""

from __future__ import print_function

import os
import random
import string
import sys
import time

import jwt
import requests

BASE_PATH = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(BASE_PATH, 'pub.key')) as f:
    PUBLIC_KEY = f.read()

with open(os.path.join(BASE_PATH, 'priv.key')) as f:
    PRIVATE_KEY = f.read()


def main():
    with open('data/hospitals.txt') as f:
        hospitals = [line.strip() for line in f.readlines() if line.strip()][:2]
        num_hospitals = len(hospitals)

    if num_hospitals < 2:
        print('There needs to be at least 2 hospitals running.')
        return False

    # Generate patient name and ID
    patient_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
    patient_id = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))

    # Create JWT token; one valid and one invalid
    valid_token = jwt.encode({
        'name': patient_name,
        'id': patient_id,
        'exp': int(time.time()) + 60,
    }, PRIVATE_KEY, algorithm='RS256').decode('utf-8')

    invalid_token = jwt.encode({
        'name': patient_name,
        'id': patient_id,
        'exp': int(time.time()) - 60,
    }, PRIVATE_KEY, algorithm='RS256').decode('utf-8')

    # print(f'[*] Created JWT: {valid_token}')
    # print(f'[*] Created JWT: {invalid_token}')

    # Register patient at hospital A
    print(f'[*] Registering name={patient_name} id={patient_id} at {hospitals[0]}...')
    res = requests.post('http://localhost:8100/patient_reg', json={
        'id': patient_id,
        'name': patient_name,
        'pub_key': PUBLIC_KEY,
    })
    res.raise_for_status()

    data = res.json()
    print(f'    Result obtained: {data}')
    patient_uid = data['uid']

    # Attempt to unregister at hospital B, there should be an error
    print(f'[*] Attempting to unregister name={patient_name} id={patient_id} at {hospitals[1]}...')
    res = requests.post('http://localhost:8101/patient_unreg', json={
        'uid': patient_uid,
        'auth_token': valid_token,
    })
    if res.status_code != 500:
        print(f'[!] Expected exception, got status {res.status_code}')
        return False
    print(f'    Exception obtained: {res.json()}')

    # Attempt to unregister at hospital A with an invalid token
    print(f'[*] Attempting to unregister name={patient_name} id={patient_id} at {hospitals[0]} with invalid token...')
    res = requests.post('http://localhost:8100/patient_unreg', json={
        'uid': patient_uid,
        'auth_token': invalid_token,
    })
    if res.status_code != 500:
        print(f'[!] Expected exception, got status {res.status_code}')
        return False
    print(f'    Exception obtained: {res.json()}')

    # Now unregister at hospital A for real
    print(f'[*] Unregistering name={patient_name} id={patient_id} at {hospitals[0]} for real this time...')
    res = requests.post('http://localhost:8100/patient_unreg', json={
        'uid': patient_uid,
        'auth_token': valid_token,
    })
    res.raise_for_status()
    print(f'    Result obtained: {res.json()}')

    # Try unregistering again?
    print(f'[*] Unregistering name={patient_name} id={patient_id} at {hospitals[0]} again!')
    res = requests.post('http://localhost:8100/patient_unreg', json={
        'uid': patient_uid,
        'auth_token': valid_token,
    })
    if res.status_code != 500:
        print(f'[!] Expected exception, got status {res.status_code}')
        return False
    print(f'    Exception obtained: {res.json()}')

    # Now register at hospital B instead
    print(f'[*] Registering name={patient_name} id={patient_id} at {hospitals[1]}...')
    res = requests.post('http://localhost:8101/patient_reg', json={
        'id': patient_id,
        'name': patient_name,
        'pub_key': PUBLIC_KEY,
    })
    res.raise_for_status()
    print(f'    Result obtained: {res.json()}')

    print()

    print('Test successful!')
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
