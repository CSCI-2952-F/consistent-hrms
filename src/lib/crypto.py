import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

def encrypt(data, pub_key):
    rsa = rsa = RSA.importKey(pub_key)
    cipher = PKCS1_v1_5.new(rsa)
    cipherText = cipher.encrypt(data.encode('utf8'))
    return base64.b64encode(ciphertext).decode('ascii')