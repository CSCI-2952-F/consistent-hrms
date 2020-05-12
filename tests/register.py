"""
Utility to register a single patient.
"""

from __future__ import print_function

import sys

from common import fail, succeed
from keys import PATIENT_NAME, PATIENT_ID, PUBLIC_KEY, PRIVATE_KEY


def main():
    with open('data/hospitals.txt') as f:
        hospitals = [line.strip() for line in f.readlines() if line.strip()]
        num_hospitals = len(hospitals)

    if num_hospitals < 1:
        print('There needs to be at least 1 hospitals running.')
        return False

    # Register patient at hospital A
    print(f'[*] Registering name={PATIENT_NAME} id={PATIENT_ID} at {hospitals[0]}...')
    res = succeed('http://localhost:8100/patient_reg', {
        'id': PATIENT_ID,
        'name': PATIENT_NAME,
        'pub_key': PUBLIC_KEY,
    })
    print(f'    Result obtained: {res}')
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
