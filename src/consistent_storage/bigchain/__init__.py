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
        self.root_url = "http://localhost:9984"
        # self.root_url = "http://bdb-server:9984"  # could be this instead???

        self.bdb = BigchainDB(self.root_url)

    def get(self, key: str) -> dict:
        res = self.bdb.get(search=key)

        if len(res) == 0:
            return {
                'exists': False,
                'value': None,
            }

        # TODO: how do we determine owner? I think we need a Hospital key somewhere
        return {
            'exists': True,
            'value': res[0]['id'],
            'is_owner': True,
            'owner': res[0]['key'],
        }

    def put(self, key: str, value: str) -> dict:
        prepared_creation_tx = self.bdb.transactions.prepare(
            operation='CREATE',
            signers=key,
            asset=value
        )

        # TODO: I think we might need a hospital's key here?
        fulfilled_creation_tx = self.bdb.transactions.fulfill(
            prepared_creation_tx, private_keys=None)

        self.bdb.transactions.send_commit(fulfilled_creation_tx)

        # TODO: we should probably check if the transaction is successful here

        return {
            'ok': True,
            'owner': key,
        }

    def remove(self, key: str) -> dict:
        raise NotImplementedError

    def transfer(self, key: str, dest: str) -> dict:
        get_res = self.get(key)

        if not get_res['exists']:
            error = 'Key does not exist'
        elif not get_res['is_owner']:
            error = 'Not owner of key'

        if error:
            return {
                'transferred': False,
                'error': error,
            }
        else:
            transfer_asset = {
                'id': get_res['value']
            }
            # TODO: We need to discuss this
            raise NotImplementedError
