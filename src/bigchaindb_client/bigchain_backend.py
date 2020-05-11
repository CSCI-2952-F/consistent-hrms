# global
from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair

# local
from lib.consistent_storage.base import BaseStorageBackend
from lib.discovery_svc import DiscoveryService

GENESIS_PUBLIC_KEY = 'BZcVfy3LgB5z1uj2HT4s2sJ8DVnW8Hzh1CJZTZecf2ac'
GENESIS_PRIVATE_KEY = 'HzKkzuCDYfppGH7vbBrXeMA6Fg6fEVAiPaeXhxmcJ9Vm'

BIGCHAIN_KEY_NAME = 'bigchaindb'
BIGCHAIN_KEY_SCHEME = 'ed25519'


class BigchaindbBackend(BaseStorageBackend):
    """
    Basic client to proxy requests from the consistent_storage Nameko server
    to the underlying bigchaindb proxy.

    Implements the BaseStorageBackend interface.
    """
    def __init__(self, bdb_root_url: str):
        self.discovery_service = DiscoveryService()
        self.public_key = ""
        self.private_key = ""

        # Fetch our hospital ID
        self.hospital_id = self.discovery_service.get_id()

        # Check if key for bigchain exists
        public_key = self.discovery_service.get_key(BIGCHAIN_KEY_NAME, True)
        private_key = self.discovery_service.get_key(BIGCHAIN_KEY_NAME, False)
        if public_key:
            self.public_key = public_key['value']
        if private_key:
            self.private_key = private_key['value']

        self._debug_print(f"Fetched public key: {self.public_key}")
        self._debug_print(f"Fetched private key: {self.private_key}")

        # If not, generate them
        if not self.public_key or not self.private_key:
            self._debug_print(f"Regenerating keys")
            keys = generate_keypair()
            self.public_key = keys.public_key
            self.private_key = keys.private_key

        # Store the keys (idempotent)
        res = self.discovery_service.put_key(BIGCHAIN_KEY_NAME, self.public_key, True, BIGCHAIN_KEY_SCHEME)
        if not res['ok']:
            raise Exception(res['error'])
        res = self.discovery_service.put_key(BIGCHAIN_KEY_NAME, self.private_key, False, BIGCHAIN_KEY_SCHEME)
        if not res['ok']:
            raise Exception(res['error'])

        # Initialize client to BigchainDB
        self.bdb = BigchainDB(bdb_root_url)

        self._debug_print("Called constructor")
        self._debug_print(f"Public key: {self.public_key}")
        self._debug_print(f"Private key: {self.private_key}")

    def _debug_print(self, msg: str) -> None:
        print(f"[{self.hospital_id}] {msg}", flush=True)

    def get(self, key: str) -> dict:
        self._debug_print(f"Called GET with key: {key}")

        res = self.bdb.assets.get(search=key)

        self._debug_print(f"Result for GET query: {res}")

        if len(res) == 0:
            return {
                'exists': False,
                'value': None,
            }

        patient_block = res[0]
        tx_block = self.bdb.transactions.retrieve(patient_block['id'])
        owner = tx_block['outputs'][0]['public_keys'][0]

        self._debug_print(f"Owner for GET query: {owner}")

        return {
            'exists': True,
            'value': res[0]['data']['patient']['public_key'],
            'is_owner': owner == self.public_key,
            'owner': owner,
        }

    def put(self, key: str, value: str) -> dict:
        self._debug_print(f"Called PUT with key: {key} and value: {value}")
        self._debug_print(f"Public key: {self.public_key}")
        self._debug_print(f"Private key: {self.private_key}")

        patient = {'data': {'patient': {'public_key': value, 'uuid': key}}}
        metadata = {'record_type': 'patient_registration', 'hospital_id': self.hospital_id}

        prepared_creation_tx = self.bdb.transactions.prepare(operation='CREATE', signers=self.public_key, asset=patient, metadata=metadata)

        fulfilled_creation_tx = self.bdb.transactions.fulfill(prepared_creation_tx, private_keys=self.private_key)

        self._debug_print(f"Fulfilled PUT tx: {fulfilled_creation_tx}")

        res_tx = self.bdb.transactions.send_commit(fulfilled_creation_tx)

        return {
            'ok': res_tx == fulfilled_creation_tx,
            'owner': self.public_key,
        }

    def init_put(self, key: str, value: str) -> dict:
        # key: patient's uuid, value: patient's public key
        # this function should only be called when initializing the bigchaindb
        self._debug_print(f"Called INIT_PUT with key: {key} and value: {value}")
        self._debug_print(f"Public key: {self.public_key}")
        self._debug_print(f"Private key: {self.private_key}")

        patient = {'data': {'patient': {'public_key': value, 'uuid': key}}}
        metadata = {'record_type': 'patient_new_registration', 'hospital_id': ""}

        self._debug_print(f"Checking if patient with uuid: {key} exists")
        if len(self.get(key)) > 0:
            self._debug_print(f"Patient with uuid: {key} already exists!!! Aborting INIT PUT ...")
            return {
                'ok': False,
                'owner': ""
            }

        prepared_creation_tx = self.bdb.transactions.prepare(operation='CREATE', signers=GENESIS_PUBLIC_KEY, asset=patient, metadata=metadata)

        fulfilled_creation_tx = self.bdb.transactions.fulfill(prepared_creation_tx, private_keys=GENESIS_PRIVATE_KEY)

        self._debug_print(f"Fulfilled PUT tx: {fulfilled_creation_tx}")

        res_tx = self.bdb.transactions.send_commit(fulfilled_creation_tx)

        return {
            'ok': res_tx == fulfilled_creation_tx,
            'owner': GENESIS_PUBLIC_KEY,
        }

    def transfer_to_register(self, key: str, value: str) -> dict:
        # key: patient's uuid, value: patient's public key
        self._debug_print(f"Called TRANSFER_TO_REGISTER with key: {key} and value: {value}")
        self._debug_print(f"Public key: {self.public_key}")
        self._debug_print(f"Private key: {self.private_key}")

        self._debug_print(f"Checking if patient with uuid: {key} exists")
        query_results = self.bdb.assets.get(search=key)
        self._debug_print(f"Query results: {query_results}")

        error = None
        if len(query_results) == 0:
            error = 'Key does not exist'

        tx_id = query_results[0]['id']
        patient_block = self.bdb.transactions.retrieve(tx_id)
        output = patient_block['outputs'][0]

        self._debug_print(f"Patient block: {patient_block}")

        if output['public_keys'][0] != GENESIS_PUBLIC_KEY:
            error = 'Genesis is not owner of key'

        if error:
            return {
                'transferred': False,
                'error': error,
            }

        patient_transfer_asset = {'id': tx_id}

        transfer_input = {
            'fulfillment': output['condition']['details'],
            'fulfills': {
                'output_index': 0,  # TODO: should this always be 0?
                'transaction_id': tx_id,
            },
            'owners_before': output['public_keys']
        }

        prepared_transfer_tx = self.bdb.transactions.prepare(
            operation='TRANSFER', asset=patient_transfer_asset, inputs=transfer_input, recipients=self.public_key
        )

        fulfilled_transfer_tx = self.bdb.transactions.fulfill(prepared_transfer_tx, private_keys=GENESIS_PRIVATE_KEY)

        res_tx = self.bdb.transactions.send_commit(fulfilled_transfer_tx)

        if res_tx != fulfilled_transfer_tx:
            return {'transferred': False, 'error': "Checksum failed"}
        else:
            return {'transferred': True}

    def remove(self, key: str) -> dict:
        raise NotImplementedError()

    def transfer(self, key: str, dest: str) -> dict:
        self._debug_print(f"Called TRANSFER with key: {key} and dest: {dest}")
        self._debug_print(f"Public key: {self.public_key}")
        self._debug_print(f"Private key: {self.private_key}")

        # assumes dest is the hospital slug
        dest_hospital = self.discovery_service.find_hospital(dest)
        dest_public_key = None

        for pubkey in dest_hospital['public_keys']:
            if pubkey['name'] == BIGCHAIN_KEY_NAME:
                dest_public_key = pubkey['value']

        if dest_public_key is None:
            # TODO: Invalid grpc error message but blah
            return {'transferred': False, 'error': 'Hospital does not exist'}

        self._debug_print(f"Destination Hospital Pub Key: {dest_public_key}")

        query_results = self.bdb.assets.get(search=key)

        self._debug_print(f"Query results: {query_results}")

        error = None
        if len(query_results) == 0:
            error = 'Key does not exist'

        tx_id = query_results[0]['id']
        patient_block = self.bdb.transactions.retrieve(tx_id)
        output = patient_block['outputs'][0]

        self._debug_print(f"Patient block: {patient_block}")

        if output['public_keys'][0] != self.public_key:
            error = 'Not owner of key'

        if error:
            return {
                'transferred': False,
                'error': output['public_keys'][0] + ' == ' + self.public_key + ' == ' + patient_block['inputs'][0]['owners_before'][0],
            }

        patient_transfer_asset = {'id': tx_id}

        transfer_input = {
            'fulfillment': output['condition']['details'],
            'fulfills': {
                'output_index': 0,  # TODO: should this always be 0?
                'transaction_id': tx_id,
            },
            'owners_before': output['public_keys']
        }

        prepared_transfer_tx = self.bdb.transactions.prepare(
            operation='TRANSFER', asset=patient_transfer_asset, inputs=transfer_input, recipients=dest_public_key
        )

        fulfilled_transfer_tx = self.bdb.transactions.fulfill(prepared_transfer_tx, private_keys=self.private_key)

        res_tx = self.bdb.transactions.send_commit(fulfilled_transfer_tx)

        if res_tx != fulfilled_transfer_tx:
            return {'transferred': False, 'error': "Checksum failed"}
        else:
            return {'transferred': True}
