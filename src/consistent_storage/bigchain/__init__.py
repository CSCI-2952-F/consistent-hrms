# standard
import base64
import os

# global
from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair

# local
from lib.consistent_storage import BaseStorageBackend
from lib.discovery_svc import DiscoveryService

GENESIS_PUBLIC_KEY = 'BZcVfy3LgB5z1uj2HT4s2sJ8DVnW8Hzh1CJZTZecf2ac'
GENESIS_PRIVATE_KEY = 'HzKkzuCDYfppGH7vbBrXeMA6Fg6fEVAiPaeXhxmcJ9Vm'


class BigchaindbBackend(BaseStorageBackend):
    """
    Basic client to proxy requests from the consistent_storage Nameko server
    to the underlying bigchaindb proxy.

    Implements the BaseStorageBackend interface.
    """
    def __init__(self, bdb_root_url: str):
        self.keys = generate_keypair()
        self.bdb = BigchainDB(bdb_root_url)

        ds = DiscoveryService()
        self.hospital_slug = ds.get_id()

        if not self._put_self_key():
            raise Exception("ERROR: Failed to put self key on bigchaindb")

    def _put_self_key(self) -> bool:
        hospital = {
            'data': {
                'public_key': self.keys.public_key,
            }
        }
        metadata = {
            'record_type': 'hospital_key',
            'index': self.hospital_slug + "-public-key",
        }

        prepared_creation_tx = self.bdb.transactions.prepare(
            operation='CREATE',
            signers=GENESIS_PUBLIC_KEY,
            asset=hospital,
            metadata=metadata
        )

        fulfilled_creation_tx = self.bdb.transactions.fulfill(
            prepared_creation_tx,
            private_keys=GENESIS_PRIVATE_KEY
        )

        res_tx = self.bdb.transactions.send_commit(fulfilled_creation_tx)

        return res_tx == fulfilled_creation_tx

    def get(self, key: str) -> dict:
        res = self.bdb.assets.get(search=key)

        if len(res) == 0:
            return {
                'exists': False,
                'value': None,
            }

        patient_block = res[0]
        tx_block = self.bdb.transactions.retrieve(patient_block['id'])
        owner = tx_block['outputs'][0]['public_keys'][0]

        return {
            'exists': True,
            'value': res[0]['data']['patient']['public_key'],
            'is_owner': owner == self.keys.public_key,
            'owner': owner,
        }

    def put(self, key: str, value: str) -> dict:
        patient = {
            'data': {
                'patient': {
                    'public_key': value,
                    'uuid': key
                }
            }
        }
        metadata = {
            'record_type': 'patient_registration',
            'hospital_slug': self.hospital_slug
        }

        prepared_creation_tx = self.bdb.transactions.prepare(
            operation='CREATE',
            signers=self.keys.public_key,
            asset=patient,
            metadata=metadata
        )

        fulfilled_creation_tx = self.bdb.transactions.fulfill(
            prepared_creation_tx,
            private_keys=self.keys.private_key
        )

        res_tx = self.bdb.transactions.send_commit(fulfilled_creation_tx)

        return {
            'ok': res_tx == fulfilled_creation_tx,
            'owner': self.keys.public_key,
        }

    def remove(self, key: str) -> dict:
        raise NotImplementedError

    def transfer(self, key: str, dest: str) -> dict:
        # assumes dest is the hospital slug
        # use dest to query blockchain to find public key of destination hospital
        destination_hospital_public_key = self._get_key_by_slug(dest)

        query_results = self.bdb.assets.get(search=key)

        if len(query_results) == 0:
            error = 'Key does not exist'

        tx_id = query_results[0]['id']
        patient_block = self.bdb.transactions.retrieve(tx_id)
        output = patient_block['outputs'][0]

        if output['public_keys'][0] != self.keys.public_key:
            error = 'Not owner of key'

        if error:
            return {
                'transferred': False,
                'error': error,
            }

        patient_transfer_asset = {
            'id': tx_id
        }

        transfer_input = {
            'fulfillment': output['condition']['details'],
            'fulfills': {
                'output_index': 0,  # TODO: should this always be 0?
                'transaction_id': tx_id
            },
            'owners_before': output['public_keys']
        }

        prepared_transfer_tx = self.bdb.transactions.prepare(
            operation='TRANSFER',
            asset=patient_transfer_asset,
            inputs=transfer_input,
            recipients=destination_hospital_public_key
        )

        fulfilled_transfer_tx = self.bdb.transactions.fulfill(
            prepared_transfer_tx,
            private_keys=self.keys.private_key
        )

        res_tx = self.bdb.transactions.send_commit(fulfilled_transfer_tx)

        if res_tx != fulfilled_transfer_tx:
            return {
                'transferred': False,
                'error': "Checksum failed"
            }
        else:
            return {
                'transferred': True
            }

    def _get_key_by_slug(self, hospital_slug: str) -> str:
        query_index = hospital_slug + '-public-key'
        res = self.bdb.metadata.get(search=query_index)

        if len(res) == 0:
            return ""

        hospital_block = res[0]
        return hospital_block['data']['public_key']
