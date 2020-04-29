"""
End-to-end test for registering a patient.

Requires at least 2 hospitals to be running. Assumes their API gateways are accessible at
ports 8100 and 8101 respectively.
"""

from __future__ import print_function

import random
import string
import sys

from common import fail, succeed
from keys import PUBLIC_KEY


def main():
    with open('data/hospitals.txt') as f:
        hospitals = [line.strip() for line in f.readlines() if line.strip()]
        num_hospitals = len(hospitals)

    if num_hospitals < 1:
        print('There needs to be at least 2 hospitals running.')
        return False

    # Generate patient name and ID
    patient_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
    patient_id = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))

    # Register patient at hospital A
    print(f'[*] Registering name={patient_name} id={patient_id} at {hospitals[0]}...')
    res = succeed('http://localhost:8100/patient_reg', {
        'id': patient_id,
        'name': patient_name,
        'pub_key': PUBLIC_KEY,
    })
    print(f'    Result obtained: {res}')

    # Attempt to register patient at hospital B
    print(f'[*] Registering name={patient_name} id={patient_id} at {hospitals[1]}...')
    res = fail('http://localhost:8101/patient_reg', {
        'id': patient_id,
        'name': patient_name,
        'pub_key': PUBLIC_KEY,
    })
    print(f'    Exception obtained: {res}')

    print()

    print('Test successful!')
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
