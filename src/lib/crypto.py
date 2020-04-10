import base64

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

import rsa
import rsa.key
import rsa.randnum

BLOCK_SIZE = 16
KEY_FORMAT = 'DER'


def generate_keys():
    return rsa.newkeys(256)


def encrypt(plaintext: str, publickey: rsa.PublicKey) -> bytes:
    # Use AES block cipher to encrypt larger chunks
    aes_key = Random.get_random_bytes(16)
    iv = Random.get_random_bytes(16)
    aes_cipher = AES.new(aes_key, AES.MODE_CBC, iv)

    # Encrypt the plaintext with the AES key
    padded = pad(plaintext.encode('utf-8'), BLOCK_SIZE)
    encrypted_text = aes_cipher.encrypt(padded)

    # Encrypt the AES cipher with RSA
    encrypted_aes_key = rsa.encrypt(aes_key, publickey)  # 32 bytes

    # Join the pieces together
    joined = encrypted_aes_key + iv + encrypted_text

    return base64.b64encode(joined)


def decrypt(ciphertext: bytes, privatekey: rsa.PrivateKey) -> str:
    # Decode the base64 encoded key + ciphertext combo
    decoded = base64.b64decode(ciphertext)

    # Split the encrypted AES key from the AES-encrypted ciphertext
    encrypted_aes_key, iv, encrypted_text = decoded[:32], decoded[32:32 + 16], decoded[32 + 16:]

    # Decrypt the AES key
    aes_key = rsa.decrypt(encrypted_aes_key, privatekey)
    aes_cipher = AES.new(aes_key, AES.MODE_CBC, iv=iv)

    # Decrypt and unpad the ciphertext
    decrypted = aes_cipher.decrypt(encrypted_text)
    decrypted_text = unpad(decrypted, BLOCK_SIZE)

    return decrypted_text.decode('utf-8')


def b64encode(key: rsa.key.AbstractKey) -> str:
    return base64.b64encode(key.save_pkcs1(format=KEY_FORMAT)).decode('utf-8')


def b64decode_pub(key: str) -> rsa.PublicKey:
    return rsa.PublicKey.load_pkcs1(key, format=KEY_FORMAT)


def b64decode_priv(key: str) -> rsa.PrivateKey:
    return rsa.PrivateKey.load_pkcs1(key, format=KEY_FORMAT)
