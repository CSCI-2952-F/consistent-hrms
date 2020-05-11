#!/usr/bin/env python
from sys import exit
from os import getenv
import traceback
import csv

from bigchaindb_client.bigchain_backend import BigchaindbBackend
from bigchaindb_driver.crypto import generate_keypair

PATH_TO_VOLUME = "/usr/src/app/bigchaindb_client/patient_cards/"


def catch_exc(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            tb = traceback.format_exc()
            _debug_print(tb)
            exit(1)

    return wrapper


@catch_exc
def prepopulate():
    bdb_root_url = getenv('BIGCHAIN_ROOT_URL')
    if not bdb_root_url:
        raise Exception('BIGCHAIN_ROOT_URL not set')

    temp_backend = BigchaindbBackend(bdb_root_url)

    for i in range(100):
        name = "bob"
        patient_id = str(i)
        uuid = name + patient_id
        keys = generate_keypair()
        temp_backend.init_put(uuid, keys.public_key)

        _debug_print(f"{uuid} with pub_key:{keys.public_key} put to bigchaindb")

        file_name = PATH_TO_VOLUME + uuid + "_patient_card.csv"
        with open(file_name, 'w') as f:
            writer = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['NAME', 'ID', 'PUB_KEY', 'PRIV_KEY'])
            writer.writerow([name, patient_id, keys.public_key, keys.private_key])

        _debug_print(f"{uuid} with priv_key:{keys.public_key} written to csv")


def _debug_print(msg: str) -> None:
    print(f"[prepopulate.py] {msg}", flush=True)


if __name__ == '__main__':
    prepopulate()
