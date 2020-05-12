"""
Utility to unregister a single patient.
"""

from __future__ import print_function

import sys
import time

import jwt

from keys import PATIENT_NAME, PATIENT_ID, PUBLIC_KEY, PRIVATE_KEY
from common import fail, succeed


def main():
    with open('data/hospitals.txt') as f:
        hospitals = [line.strip() for line in f.readlines() if line.strip()][:2]

    valid_token = jwt.encode({
        'name': PATIENT_NAME,
        'id': PATIENT_ID,
        'exp': int(time.time()) + 60,
    }, PRIVATE_KEY, algorithm='RS256').decode('utf-8')

    uid = PATIENT_NAME + PATIENT_ID

    print(f'[*] Unregistering uid={uid} at {hospitals[0]}...')
    res = succeed('http://localhost:8100/patient_unreg', {
        'uid': uid,
        'auth_token': valid_token,
    })
    print(f'    Result obtained: {res}')
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
