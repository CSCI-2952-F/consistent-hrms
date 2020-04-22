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

from keys import PRIVATE_KEY, PUBLIC_KEY
from common import fail, succeed


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

    # Register patient at hospital A
    print(f'[*] Registering name={patient_name} id={patient_id} at {hospitals[0]}...')
    res = succeed('http://localhost:8100/patient_reg', {
        'id': patient_id,
        'name': patient_name,
        'pub_key': PUBLIC_KEY,
    })
    print(f'    Result obtained: {res}')
    patient_uid = res['uid']

    # Attempt to unregister at hospital B, there should be an error
    print(f'[*] Attempting to unregister uid={patient_uid} at {hospitals[1]}...')
    res = fail('http://localhost:8101/patient_unreg', {
        'uid': patient_uid,
        'auth_token': valid_token,
    })
    print(f'    Exception obtained: {res}')

    # Attempt to unregister at hospital A with an invalid token
    print(f'[*] Attempting to unregister uid={patient_uid} at {hospitals[0]} with invalid token...')
    res = fail('http://localhost:8100/patient_unreg', {
        'uid': patient_uid,
        'auth_token': invalid_token,
    })
    print(f'    Exception obtained: {res}')

    # Now unregister at hospital A for real
    print(f'[*] Unregistering uid={patient_uid} at {hospitals[0]} for real this time...')
    res = succeed('http://localhost:8100/patient_unreg', {
        'uid': patient_uid,
        'auth_token': valid_token,
    })
    print(f'    Result obtained: {res}')

    # Try unregistering again?
    print(f'[*] Unregistering uid={patient_uid} at {hospitals[0]} again!')
    res = fail('http://localhost:8100/patient_unreg', {
        'uid': patient_uid,
        'auth_token': valid_token,
    })
    print(f'    Exception obtained: {res}')

    # Now register at hospital B instead
    print(f'[*] Registering uid={patient_uid} at {hospitals[1]}...')
    res = succeed('http://localhost:8101/patient_reg', {
        'id': patient_id,
        'name': patient_name,
        'pub_key': PUBLIC_KEY,
    })
    print(f'    Result obtained: {res}')

    print()

    print('Test successful!')
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
