import base64

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA


def encrypt(data, pub_key):
    rsa = RSA.importKey(pub_key)
    cipher = PKCS1_v1_5.new(rsa)
    cipherText = cipher.encrypt(data.encode('utf-8'))
    return base64.b64encode(cipherText).decode('utf-8')
