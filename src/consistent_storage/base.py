from typing import Tuple


class BaseSagasClient:
    def get(self, key: str) -> dict:
        raise NotImplementedError()

    def put(self, key: str, value: str) -> bool:
        raise NotImplementedError()

    def remove(self, key: str) -> bool:
        raise NotImplementedError()


class KeyExistsError(Exception):
    def __init__(self, key):
        super().__init__(f'Key "{key}" already exists')
