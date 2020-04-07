"""
Filesystem-backed persistent sagas storage. Slow but simple to use.
Supports versioning of keys to identify different versions of the same key.
"""

from lib import jsonfile

from consistent_storage.sagas.persistent import BasePersistentSagasStorage


class PersistentSagasFileStorage(BasePersistentSagasStorage):
    def __init__(self, filepath):
        self.filepath = filepath
        jsonfile.touch(filepath)

    def _get(self, key):
        try:
            return jsonfile.get_path(self.filepath, key)
        except KeyError:
            return None

    def _set(self, key, value):
        jsonfile.set_path(self.filepath, key, value)
