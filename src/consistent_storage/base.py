class BaseSagasClient:
    def get(self, key: str) -> bytes:
        raise NotImplementedError()

    def put(self, key: str, value: str) -> bool:
        raise NotImplementedError()

    def remove(self, key: str) -> bool:
        raise NotImplementedError()
