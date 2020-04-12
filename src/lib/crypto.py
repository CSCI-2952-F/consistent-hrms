import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

KEY_FORMAT = 'DER'

def encrypt(data, pub_key):
    rsa = RSA.importKey(pub_key)
    cipher = PKCS1_v1_5.new(rsa)
    cipherText = cipher.encrypt(data.encode('utf8'))
    return base64.b64encode(cipherText).decode('ascii')