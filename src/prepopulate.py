#!/usr/bin/env python
import sys
from os import getenv
import traceback
import csv

from bigchaindb_client.bigchain_backend import BigchaindbBackend
from lib import crypto

PATH_TO_VOLUME = "/usr/src/app/bigchaindb_client/patient_cards/"


def catch_exc(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            tb = traceback.format_exc()
            _debug_print(tb)
            sys.exit(1)

    return wrapper


@catch_exc
def prepopulate(num_cards, name):
    bdb_root_url = getenv('BIGCHAIN_ROOT_URL')
    if not bdb_root_url:
        raise Exception('BIGCHAIN_ROOT_URL not set')

    temp_backend = BigchaindbBackend(bdb_root_url)

    for i in range(num_cards):
        patient_id = str(i)
        uuid = name + patient_id

        _debug_print("Generating keys...")
        public_key, private_key = crypto.generate_keys()
        public_key = crypto.export_key(public_key)
        private_key = crypto.export_key(private_key)

        res = temp_backend.init_put(uuid, public_key)

        if not res['ok']:
            _debug_print("INIT PUT failed, aborting this PUT ...")
            continue

        _debug_print(f"{uuid} with pub_key:{public_key} put to bigchaindb")

        file_name = PATH_TO_VOLUME + uuid + "_patient_card.csv"
        with open(file_name, 'w') as f:
            writer = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['NAME', 'ID', 'PUB_KEY', 'PRIV_KEY'])
            writer.writerow([name, patient_id, public_key, private_key])

        _debug_print(f"{uuid} with priv_key:{public_key} written to csv")


def _debug_print(msg: str) -> None:
    print(f"[prepopulate.py] {msg}", flush=True)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: prepopulate.py <num_cards> <patient_name>')
        print('Example: prepopulate.py 1 "alice"')
        sys.exit(1)

    prepopulate(int(sys.argv[1]), sys.argv[2])
