from typing import Tuple


class BaseStorageBackend:
    """
    Interface for consistent storage backends to implement.
    """
    def get(self, key: str) -> dict:
        """
        Fetches a key from consistent storage, and returns a dictionary as follows:

        {
            'exists': [bool],
            'value': [str or NoneType],
            'is_owner': [bool],
            'owner': [str],
        }

        If the key does not exist, the `is_owner` and `owner` metadata keys may not
        be present in the returned dictionary.
        """
        raise NotImplementedError()

    def put(self, key: str, value: str) -> dict:
        """
        Stores a key in consistent storage. Fails if the key is already present
        and stored by another owner.

        The semantics of this operation is that all such operations are atomic, or
        linearizable. This means that a Put operation for a key K that succeeds on
        this client is guaranteed to fail for all other clients trying to Put the
        same key K.

        Returns a dictionary as follows:

        {
            'ok': [bool],
            'owner': [str],
        }

        Arguments:
            key {str} -- Key to store.
            value {str} -- Value to store in the consistent storage.
        """
        raise NotImplementedError()

    def remove(self, key: str) -> dict:
        """
        Removes a key in consistent storage, in a linearizable fashion.
        Fails if the key is not in storage, or is owned by another owner.

        Returns a dictionary as follows:

        {
            'removed': [bool],
            'error': [str],
        }

        Arguments:
            key {str} -- Key to remove.
        """
        raise NotImplementedError()

    def transfer(self, key: str, dest: str) -> dict:
        """
        Transfers a key to a new destination owner.
        Fails if the key is not in storage, or is owned by another owner.

        Ideally, the destination hospital name should be retrieved and validated against
        a central registry of hospitals (e.g. ZooKeeper).

        Returns a dictionary as follows:

        {
            'transferred': [bool],
            'error': [str],
        }

        Arguments:
            key {str} -- Key to transfer.
            dest {str} -- Destination hospital name.
        """
        raise NotImplementedError()
