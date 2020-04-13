import base64

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA


def encrypt(data, pub_key):
    rsa = RSA.importKey(pub_key)
    cipher = PKCS1_v1_5.new(rsa)
    cipher_text = cipher.encrypt(data.encode('utf-8'))
    return base64.b64encode(cipher_text).decode('utf-8')
