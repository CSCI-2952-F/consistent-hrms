import hashlib


def get_partition(key: str, partitions: int) -> int:
    h = hashlib.sha256()
    h.update(key.encode('utf-8'))
    h_int = int.from_bytes(h.digest(), "big")
    return h_int % partitions
