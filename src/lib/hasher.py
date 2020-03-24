import hashlib as hasher
"""
External hasher service that all hospitals use.
"""


def hash(data):
    h = hasher.sha256()
    result = str(data)
    h.update(result.encode('utf-8'))
    return h.hexdigest()
