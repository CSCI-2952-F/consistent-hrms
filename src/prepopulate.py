#!/usr/bin/env python
import sys
from os import getenv
import traceback
import csv

from lib import hasher
from bigchaindb_client.bigchain_backend import BigchaindbBackend
from lib import crypto, hasher

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

    _debug_print("Generating keys...")
    public_key, private_key = crypto.generate_keys()
    public_key = crypto.export_key(public_key)
    private_key = crypto.export_key(private_key)

    for i in range(num_cards):
        patient_id = str(i)
        hash_uid = hasher.hash(name + patient_id)

        res = temp_backend.init_put(hash_uid, public_key)

        if not res['ok']:
            _debug_print("INIT PUT failed, aborting this PUT ...")
            continue

        _debug_print(f"{hash_uid} with pub_key:{public_key} put to bigchaindb")

        file_name = PATH_TO_VOLUME + name + patient_id + "_patient_card.csv"

        with open(file_name, 'w') as f:
            writer = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['NAME', 'ID', 'PUB_KEY', 'PRIV_KEY'])
            writer.writerow([name, patient_id, public_key, private_key])

        _debug_print(f"{hash_uid} with priv_key:{public_key} written to csv")


def _debug_print(msg: str) -> None:
    print(f"[prepopulate.py] {msg}", flush=True)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: prepopulate.py <num_cards> <patient_name>')
        print('Example: prepopulate.py 1 "alice"')
        sys.exit(1)

    prepopulate(int(sys.argv[1]), sys.argv[2])
