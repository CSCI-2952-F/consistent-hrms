"""
End-to-end test for registering a patient.

Requires at least 2 hospitals to be running. Assumes their API gateways are accessible at
ports 8100 and 8101 respectively.
"""

from __future__ import print_function

import base64
import sys
import time

import jwt
import rsa

from common import fail, succeed
from keys import PATIENT_NAME, PATIENT_ID, PUBLIC_KEY, PRIVATE_KEY


def main():
    with open('data/hospitals.txt') as f:
        hospitals = [line.strip() for line in f.readlines() if line.strip()]
        num_hospitals = len(hospitals)

    if num_hospitals < 2:
        print('There needs to be at least 2 hospitals running.')
        return False

    # Register patient at hospital A
    print(f'[*] Registering name={PATIENT_NAME} id={PATIENT_ID} at {hospitals[0]}...')
    res = succeed('http://localhost:8100/patient_reg', {
        'id': PATIENT_ID,
        'name': PATIENT_NAME,
        'pub_key': PUBLIC_KEY,
    })
    print(f'    Result obtained: {res}')

    patient_uid = res['uid']

    # Attempt to register patient at hospital B
    print(f'[*] Registering name={PATIENT_NAME} id={PATIENT_ID} at {hospitals[1]}...')
    res = fail('http://localhost:8101/patient_reg', {
        'id': PATIENT_ID,
        'name': PATIENT_NAME,
        'pub_key': PUBLIC_KEY,
    })
    print(f'    Exception obtained: {res}')

    # Read patient card from hospital A
    print(f'[*] Fetching patient data for name={PATIENT_NAME} id={PATIENT_ID} from {hospitals[0]}...')
    res = succeed('http://localhost:8100/patient_read', {
        'uid': patient_uid,
    })
    data_len = len(res['data'])
    print(f'    Result obtained: data=[{data_len} items]')

    # Decrypt patient data
    print(f'[*] Decrypting patient data for name={PATIENT_NAME} id={PATIENT_ID} from {hospitals[0]}...')
    priv_key = rsa.PrivateKey.load_pkcs1(PRIVATE_KEY)
    for data in res['data']:
        data = base64.b64decode(data.encode('utf-8'))
        decrypted = rsa.decrypt(data, priv_key).decode('utf-8')
        print(f'    Result obtained: {decrypted}')

    # Clean up: Unregister patient
    token = jwt.encode({
        'name': PATIENT_NAME,
        'id': PATIENT_ID,
        'exp': int(time.time()) + 60,
    }, PRIVATE_KEY, algorithm='RS256').decode('utf-8')

    print(f'[*] Unregistering uid={patient_uid} at {hospitals[0]}...')
    res = succeed('http://localhost:8100/patient_unreg', {
        'uid': patient_uid,
        'auth_token': token,
    })
    print(f'    Result obtained: {res}')

    print()

    print('Test successful!')
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
