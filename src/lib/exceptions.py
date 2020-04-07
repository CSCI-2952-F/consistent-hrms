class KeyExistsError(Exception):
    def __init__(self, key):
        super().__init__(f'Key "{key}" already exists')
