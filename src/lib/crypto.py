import base64

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

import rsa
import rsa.key

KEY_FORMAT = 'DER'
BITSIZE = 2048


def generate_keys():
    return rsa.newkeys(BITSIZE)


# TODO: https://github.com/irvinlim/cs2952f-hrms/blob/0b2fc4647fa7408dcb3d942c899eba5027dde481/src/lib/crypto.py
# Re-Add AEX block cipher encryption here and in js code.
def encrypt(data, pub_key):
    rsa = RSA.importKey(pub_key)
    cipher = PKCS1_v1_5.new(rsa)
    cipher_text = cipher.encrypt(data.encode('utf-8'))
    return base64.b64encode(cipher_text).decode('utf-8')


def load_privkey(keystr: str) -> rsa.PrivateKey:
    return rsa.PrivateKey.load_pkcs1(keystr)


def load_pubkey(keystr: str) -> rsa.PublicKey:
    return rsa.PublicKey.load_pkcs1(keystr)


def sign(data: bytes, priv_key: rsa.PrivateKey) -> bytes:
    "Returns a signature of the data."
    return rsa.sign(data, priv_key, hash_method='SHA-256')


def verify(data: bytes, signature: str, pub_key: rsa.PublicKey) -> bool:
    "Verifies a signature of the data."
    try:
        rsa.verify(data, bytearray.fromhex(signature), pub_key)
        return True
    except rsa.VerificationError:
        return False


def export_key(key: rsa.key.AbstractKey) -> str:
    key_bytes = key.save_pkcs1(format='PEM')
    return key_bytes.decode('utf-8')
