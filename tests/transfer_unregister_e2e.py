"""
End-to-end test for transferring a patient registration from hospital A to B, and
then unregistering the patient at hospital B.
"""

from __future__ import print_function

import random
import re
import string
import sys
import time

import jwt

from common import fail, succeed
from keys import PRIVATE_KEY, PUBLIC_KEY


def main():
    with open('data/hospitals.txt') as f:
        hospitals = [line.strip() for line in f.readlines() if line.strip()]
        slugs = [re.sub('[^a-z]+', '-', name.lower()) for name in hospitals]
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

    # Transfer to B
    print(f'[*] Transferring uid={patient_uid} from {hospitals[0]} to {hospitals[1]} for real this time...')
    res = succeed('http://localhost:8100/patient_transfer', {
        'uid': patient_uid,
        'auth_token': valid_token,
        'dest_hospital': slugs[1],
    })
    print(f'    Result obtained: {res}')

    # Unregister at hospital B
    print(f'[*] Unregistering uid={patient_uid} at {hospitals[1]}...')
    res = succeed('http://localhost:8101/patient_unreg', {
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
