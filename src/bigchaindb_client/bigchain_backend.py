# global
from bigchaindb_driver import BigchainDB
# from bigchaindb_driver.crypto import generate_keypair

# local
from lib.consistent_storage.base import BaseStorageBackend
from lib.discovery_svc import DiscoveryService

# GENESIS_PUBLIC_KEY = 'BZcVfy3LgB5z1uj2HT4s2sJ8DVnW8Hzh1CJZTZecf2ac'
# GENESIS_PRIVATE_KEY = 'HzKkzuCDYfppGH7vbBrXeMA6Fg6fEVAiPaeXhxmcJ9Vm'


class BigchaindbBackend(BaseStorageBackend):
    """
    Basic client to proxy requests from the consistent_storage Nameko server
    to the underlying bigchaindb proxy.

    Implements the BaseStorageBackend interface.
    """
    def __init__(self, bdb_root_url: str):
        self.discovery_service = DiscoveryService()
        self.hospital_id = self.discovery_service.get_id()

        hospital = self.discovery_service.find_hospital(self.hospital_id)

        self.public_key = hospital['public_key']
        self.private_key = self.discovery_service.get_private_key()

        self.bdb = BigchainDB(bdb_root_url)

        self._debug_print("Called constructor")
        self._debug_print(f"Public key: {self.public_key}")
        self._debug_print(f"Private key: {self.private_key}")

        # if not self._put_self_key():
        #     raise Exception("ERROR: Failed to put self key on bigchaindb")

    def _debug_print(self, msg: str) -> None:
        print(f"[{self.hospital_id}] {msg}", flush=True)

    # def _put_self_key(self) -> bool:
    #     self._debug_print("Called _put_self_key()")
    #     self._debug_print(f"Public key: {self.keys.public_key}")
    #     self._debug_print(f"Private key: {self.keys.private_key}")
    #
    #     hospital = {
    #         'data': {
    #             self.hospital_slug + '_public_key': self.keys.public_key,
    #         }
    #     }
    #     metadata = {
    #         'record_type': 'hospital_key',
    #     }
    #
    #     prepared_creation_tx = self.bdb.transactions.prepare(
    #         operation='CREATE', signers=GENESIS_PUBLIC_KEY, asset=hospital, metadata=metadata
    #     )
    #
    #     fulfilled_creation_tx = self.bdb.transactions.fulfill(prepared_creation_tx, private_keys=GENESIS_PRIVATE_KEY)
    #
    #     res_tx = self.bdb.transactions.send_commit(fulfilled_creation_tx)
    #
    #     return res_tx == fulfilled_creation_tx

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

    def remove(self, key: str) -> dict:
        raise NotImplementedError()

    def transfer(self, key: str, dest: str) -> dict:
        self._debug_print(f"Called TRANSFER with key: {key} and dest: {dest}")
        self._debug_print(f"Public key: {self.public_key}")
        self._debug_print(f"Private key: {self.private_key}")

        # assumes dest is the hospital slug
        # use dest to query blockchain to find public key of destination hospital
        dest_hospital = self.discovery_service.find_hospital(dest)
        dest_public_key = dest_hospital.publicKey

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

    # def _get_key_by_slug(self, hospital_slug: str) -> str:
    #     self._debug_print(f"Called _get_key_by_slug with hospital_slug: {hospital_slug}")
    #     self._debug_print(f"Public key: {self.keys.public_key}")
    #     self._debug_print(f"Private key: {self.keys.private_key}")
    #
    #     query_index = hospital_slug + '_public_key'
    #     res = self.bdb.assets.get(search=query_index)
    #
    #     self._debug_print(f"Results of query: {res}")
    #
    #     if len(res) == 0:
    #         return ""
    #
    #     hospital_block = res[0]
    #
    #     return hospital_block['data'][query_index]
