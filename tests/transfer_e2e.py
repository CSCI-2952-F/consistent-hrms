"""
End-to-end test for transferring a patient registration between hospitals.

Requires at least 2 hospitals to be running. Assumes their API gateways are accessible at
ports 8100 and 8101 respectively.
"""

from __future__ import print_function

import re
import sys
import time

import jwt

from common import fail, succeed
from keys import PATIENT_NAME, PATIENT_ID, PUBLIC_KEY, PRIVATE_KEY


def main():
    with open('data/hospitals.txt') as f:
        hospitals = [line.strip() for line in f.readlines() if line.strip()]
        slugs = [re.sub('[^a-z]+', '-', name.lower()) for name in hospitals]
        num_hospitals = len(hospitals)

    if num_hospitals < 2:
        print('There needs to be at least 2 hospitals running.')
        return False

    # Create JWT token; one valid and one invalid
    valid_token = jwt.encode({
        'name': PATIENT_NAME,
        'id': PATIENT_ID,
        'exp': int(time.time()) + 60,
    }, PRIVATE_KEY, algorithm='RS256').decode('utf-8')

    invalid_token = jwt.encode({
        'name': PATIENT_NAME,
        'id': PATIENT_ID,
        'exp': int(time.time()) - 60,
    }, PRIVATE_KEY, algorithm='RS256').decode('utf-8')

    # Register patient at hospital A
    print(f'[*] Registering name={PATIENT_NAME} id={PATIENT_ID} at {hospitals[0]}...')
    res = succeed('http://localhost:8100/patient_reg', {
        'id': PATIENT_ID,
        'name': PATIENT_NAME,
        'pub_key': PUBLIC_KEY,
    })

    print(f'    Result obtained: {res}')
    patient_uid = res['uid']

    # Attempt to transfer from hospital B, there should be an error
    print(f'[*] Attempting to transfer uid={patient_uid} from {hospitals[1]} to {hospitals[0]}...')
    res = fail('http://localhost:8101/patient_transfer', {
        'uid': patient_uid,
        'auth_token': valid_token,
        'dest_hospital': slugs[0],
    })
    print(f'    Exception obtained: {res}')

    # Attempt to transfer from hospital A with an invalid token
    print(f'[*] Attempting to transfer uid={patient_uid} from {hospitals[0]} to {hospitals[1]} with invalid token...')
    res = fail('http://localhost:8100/patient_transfer', {
        'uid': patient_uid,
        'auth_token': invalid_token,
        'dest_hospital': slugs[1],
    })
    print(f'    Exception obtained: {res}')

    # Attempt to transfer from hospital A to hospital A
    print(f'[*] Attempting to transfer uid={patient_uid} from {hospitals[0]} to {hospitals[0]}...')
    res = fail('http://localhost:8100/patient_transfer', {
        'uid': patient_uid,
        'auth_token': valid_token,
        'dest_hospital': slugs[0],
    })
    print(f'    Exception obtained: {res}')

    # Now transfer from hospital A to hospital B for real
    print(f'[*] Transferring uid={patient_uid} from {hospitals[0]} to {hospitals[1]} for real this time...')
    res = succeed('http://localhost:8100/patient_transfer', {
        'uid': patient_uid,
        'auth_token': valid_token,
        'dest_hospital': slugs[1],
    })
    print(f'    Result obtained: {res}')

    # Try transferring again?
    print(f'[*] Transferring uid={patient_uid} from {hospitals[0]} to {hospitals[1]} again!')
    res = fail('http://localhost:8100/patient_transfer', {
        'uid': patient_uid,
        'auth_token': valid_token,
        'dest_hospital': slugs[1],
    })
    print(f'    Exception obtained: {res}')

    # Attempt to unregister at hospital A
    print(f'[*] Attempting to unregister uid={patient_uid} at {hospitals[0]}...')
    res = fail('http://localhost:8100/patient_unreg', {
        'uid': patient_uid,
        'auth_token': valid_token,
    })
    print(f'    Exception obtained: {res}')

    # Transfer from hospital B back to hospital A
    print(f'[*] Transferring uid={patient_uid} from {hospitals[1]} to {hospitals[0]}...')
    res = succeed('http://localhost:8101/patient_transfer', {
        'uid': patient_uid,
        'auth_token': valid_token,
        'dest_hospital': slugs[0],
    })
    print(f'    Result obtained: {res}')

    # Now we can unregister at hospital A
    print(f'[*] Unregistering uid={patient_uid} at {hospitals[0]}...')
    res = succeed('http://localhost:8100/patient_unreg', {
        'uid': patient_uid,
        'auth_token': valid_token,
    })
    print(f'    Result obtained: {res}')

    print()

    print('Test successful!')
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
