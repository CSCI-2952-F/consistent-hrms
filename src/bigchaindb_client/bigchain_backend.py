import json

from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair

from lib.consistent_storage.base import BaseStorageBackend
from lib.discovery_svc import DiscoveryService

GENESIS_PUBLIC_KEY = 'BZcVfy3LgB5z1uj2HT4s2sJ8DVnW8Hzh1CJZTZecf2ac'
GENESIS_PRIVATE_KEY = 'HzKkzuCDYfppGH7vbBrXeMA6Fg6fEVAiPaeXhxmcJ9Vm'

BIGCHAIN_KEY_NAME = 'bigchaindb'
BIGCHAIN_KEY_SCHEME = 'ed25519'


class MissingAssetException(Exception):
    def __init__(self, key):
        super().__init__(f"Patient asset not yet created: {key}. Run prepopulate to get a patient card first.")


class NotOwnerException(Exception):
    def __init__(self, owner):
        self.owner = owner
        super().__init__("Not owner")


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
        if len(res) == 0:
            raise MissingAssetException(key)

        asset_id = res[0]['id']
        owner = self.bdb.transactions.get(asset_id=asset_id)[-1]['outputs'][0]['public_keys'][0]
        self._debug_print(f"Owner for {key}: {owner}")

        # If genesis owns the asset, then patient is not registered on any hospital.
        if owner == GENESIS_PUBLIC_KEY:
            return {'exists': False}

        return {
            'exists': True,
            'value': res[0]['data']['patient']['public_key'],
            'is_owner': owner == self.public_key,
            'owner': owner,
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

        try:
            asset_id, _ = self._bdb_get_latest_txn(key)
            asset_exists = True
        except MissingAssetException:
            asset_exists = False

        if asset_exists:
            self._debug_print(f"Asset already exists for {key}. Asset ID: {asset_id}")
            return {
                'ok': False,
                'owner': '',
            }

        prepared_creation_tx = self.bdb.transactions.prepare(
            operation='CREATE',
            signers=GENESIS_PUBLIC_KEY,
            asset=patient,
            metadata=metadata,
        )

        fulfilled_creation_tx = self.bdb.transactions.fulfill(
            prepared_creation_tx,
            private_keys=GENESIS_PRIVATE_KEY,
        )

        self._debug_print(f"Fulfilled PUT tx: {fulfilled_creation_tx}")

        res_tx = self.bdb.transactions.send_commit(fulfilled_creation_tx)

        return {'ok': res_tx == fulfilled_creation_tx, 'owner': GENESIS_PUBLIC_KEY}

    def put(self, key: str, value: str) -> dict:
        # key: patient's uuid, value: patient's public key
        self._debug_print(f"Called TRANSFER_TO_REGISTER with key: {key} and value: {value}")
        self._debug_print(f"Public key: {self.public_key}")
        self._debug_print(f"Private key: {self.private_key}")

        # Transfer from genesis to ourselves.
        try:
            new_owner = self._bdb_transfer(key, GENESIS_PUBLIC_KEY, GENESIS_PRIVATE_KEY, self.public_key)
        except NotOwnerException as e:
            return {'ok': False, 'owner': e.owner}

        if new_owner != self.public_key:
            self._debug_print(f"PUT failed, another transaction beat us to it: {new_owner}")
            return {'ok': False}

        self._debug_print(f"Successfully PUT key {key}. New owner: {new_owner}")
        return {'ok': True, 'owner': self.public_key}

    def remove(self, key: str) -> dict:
        self._debug_print(f"Called REMOVE with key: {key}")
        self._debug_print(f"Public key: {self.public_key}")
        self._debug_print(f"Private key: {self.private_key}")

        # Transfer from ourselves to genesis.
        try:
            new_owner = self._bdb_transfer(key, self.public_key, self.private_key, GENESIS_PUBLIC_KEY)
        except NotOwnerException:
            return {'removed': False, 'error': 'Not owner of key'}

        if new_owner != GENESIS_PUBLIC_KEY:
            self._debug_print(f"REMOVE failed, another transaction beat us to it: {new_owner}")
            return {'removed': False, 'error': 'Transaction failed'}

        self._debug_print(f"Successfully REMOVE key {key}. New owner: {new_owner}")
        return {'removed': True}

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
                break

        if dest_public_key is None:
            return {'transferred': False, 'error': 'Hospital does not exist'}
        self._debug_print(f"Destination Hospital Pub Key: {dest_public_key}")

        # Transfer from genesis to ourselves.
        try:
            new_owner = self._bdb_transfer(key, self.public_key, self.private_key, dest_public_key)
        except NotOwnerException:
            return {'transferred': False, 'error': 'Not owner of key'}

        if new_owner is None:
            self._debug_print(f"TRANSFER failed, another transaction beat us to it: {new_owner}")
            return {'transferred': False, 'error': 'Transaction failed'}

        self._debug_print(f"Successfully TRANSFER key {key}. New owner: {new_owner}")
        return {'transferred': True}

    def _bdb_get_latest_txn(self, key):
        "Returns latest transaction of an asset named by key."

        # Search for the asset.
        # NOTE: This does a FULLTEXT search. So that means keys should be unique enough.
        query_results = self.bdb.assets.get(search=key)

        if len(query_results) == 0:
            raise MissingAssetException(key)

        # Get asset ID.
        asset_id = query_results[0]['id']

        # Look up all transactions for this asset.
        transactions = self.bdb.transactions.get(asset_id=asset_id)

        # Uncomment this to see the list of past transactions
        # past_txns = [{'public_key': txn['outputs'][0]['public_keys'][0], 'txn_id': txn['id']} for txn in transactions]
        # self._debug_print('Past transactions: {}'.format(json.dumps(past_txns, indent=2)))

        return asset_id, transactions[-1]

    def _bdb_transfer(self, key, from_public_key, from_private_key, to_public_key):
        # Get latest transaction
        asset_id, txn = self._bdb_get_latest_txn(key)

        # Get the output from the latest transaction.
        output = txn['outputs'][0]

        # Get the owner from the latest transaction.
        owner = output['public_keys'][0]

        # Check if the owner matches the from_private_key.
        if owner != from_public_key:
            raise NotOwnerException(owner)

        # Prepare transaction to transfer to `to_public_key`.
        prepared_transfer_tx = self.bdb.transactions.prepare(
            operation='TRANSFER',
            asset={'id': asset_id},
            inputs={
                'fulfillment': output['condition']['details'],
                'fulfills': {
                    'output_index': 0,  # TODO: should this always be 0?
                    'transaction_id': txn['id'],  # Use latest txn ID - this new txn fulfils it
                },
                'owners_before': output['public_keys'],
            },
            recipients=to_public_key,
        )

        # Fulfil the transaction with from_private_key.
        fulfilled_transfer_tx = self.bdb.transactions.fulfill(
            prepared_transfer_tx,
            private_keys=from_private_key,
        )

        # Commit the transaction
        sent_transfer_tx = self.bdb.transactions.send_commit(fulfilled_transfer_tx)

        # Get the owner of the sent transaction
        new_owner = sent_transfer_tx['outputs'][0]['public_keys'][0]

        return new_owner
