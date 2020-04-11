from typing import Tuple


class BaseClient:
    def get(self, key: str) -> dict:
        """
        Fetches a key from consistent storage, and returns a dictionary as follows:

        {
            'value': [base64-encoded bytes or NoneType],
            'is_owner': [bool],
            'owner': [str],
        }

        The underlying storage backends store bytes for the value type, which makes
        it agnostic to the type and encoding of data to be stored. However, a bytes
        type is not serializable by Nameko and thus have to be base64-encoded.
        """
        raise NotImplementedError()

    def put(self, key: str, value: bytes) -> bool:
        """
        Stores a key in consistent storage. Fails if the key is already present
        and stored by another owner.

        The semantics of this operation is that all such operations are atomic, or
        linearizable. This means that a Put operation for a key K that succeeds on
        this client is guaranteed to fail for all other clients trying to Put the
        same key K.

        Arguments:
            key {str} -- Key to store.
            value {bytes} -- Value to store in the consistent storage.

        Returns:
            bool -- Returns True if the Put operation was successful, or False if
                    the key is already owned by another owner.
        """
        raise NotImplementedError()

    def remove(self, key: str) -> bool:
        """
        Removes a key in consistent storage, in a linearizable fashion.
        Fails if the key is not in storage, or is owned by another owner.

        Arguments:
            key {str} -- Key to remove.

        Returns:
            bool -- Returns True if the key was successfully removed, or
                    False if there is insufficient permissions to remove
                    the key.
        """
        raise NotImplementedError()


class KeyExistsError(Exception):
    def __init__(self, key):
        super().__init__(f'Key "{key}" already exists')
