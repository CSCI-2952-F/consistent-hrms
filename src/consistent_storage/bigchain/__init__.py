# standard
import base64
import os

# local
from src.bigchaindb.bigchaindb_driver import BigchainDB
from lib.consistent_storage import BaseStorageBackend


class BigchaindbBackend(BaseStorageBackend):
    """
    Basic client to proxy requests from the consistent_storage Nameko server
    to the underlying bigchaindb proxy.

    Implements the BaseStorageBackend interface.
    """
    def __init__(self):
        self.bdb = BigchainDB("http://0.0.0.0:9984")

    def get(self, key: str) -> dict:
        query_hospital_public_key = None  # TODO: where do we get this from?

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
            'is_owner': owner == query_hospital_public_key,
            'owner': owner,
        }

    def put(self, key: str, value: str) -> dict:
        hospital_public_key = None  # TODO: where do we get this from?
        hospital_private_key = None  # TODO: where do we get this from?

        patient = {
            'data': {
                'patient': {
                    'public_key': value,
                    'uuid': key
                }
            }
        }
        metadata = {
            'patient': 'registration',
            'hospital_name': None  # TODO
        }

        prepared_creation_tx = self.bdb.transactions.prepare(
            operation='CREATE',
            signers=hospital_public_key,
            asset=patient,
            metadata=metadata
        )

        fulfilled_creation_tx = self.bdb.transactions.fulfill(
            prepared_creation_tx,
            private_keys=hospital_private_key
        )

        res_tx = self.bdb.transactions.send_commit(fulfilled_creation_tx)

        return {
            'ok': res_tx == fulfilled_creation_tx,
            'owner': hospital_public_key,
        }

    def remove(self, key: str) -> dict:
        raise NotImplementedError

    def transfer(self, key: str, dest: str) -> dict:
        source_hospital_public_key = None  # TODO: where do we get this from?
        source_hospital_private_key = None  # TODO: where do we get this from?
        destination_hospital_public_key = None  # TODO: where do we get this from?

        query_results = self.bdb.assets.get(search=key)

        if len(query_results) == 0:
            error = 'Key does not exist'

        tx_id = query_results[0]['id']
        patient_block = self.bdb.transactions.retrieve(tx_id)
        output = patient_block['outputs'][0]

        if output['public_keys'][0] != source_hospital_public_key:
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
            private_keys=source_hospital_private_key
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
