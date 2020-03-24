import base64

from Crypto import Random
from Crypto.PublicKey import RSA


def generate_keys():
    modulus_length = 256 * 4
    privatekey = RSA.generate(modulus_length, Random.new().read)
    publickey = privatekey.publickey()
    return privatekey, publickey


def encrypt(message, publickey):
    encrypted_msg = publickey.encrypt(message, 32)[0]
    encoded_encrypted_msg = base64.b64encode(encrypted_msg)
    return encoded_encrypted_msg


def decrypt(encoded_encrypted_msg, privatekey):
    decoded_encrypted_msg = base64.b64decode(encoded_encrypted_msg)
    decoded_decrypted_msg = privatekey.decrypt(decoded_encrypted_msg)
    return decoded_decrypted_msg


def b64encode(key: RSA._RSAobj) -> str:
    return base64.b64encode(key.exportKey(format='DER')).decode('utf-8')


def b64decode(key: str) -> RSA._RSAobj:
    return RSA.importKey(base64.b64decode(key.encode('utf-8')))
