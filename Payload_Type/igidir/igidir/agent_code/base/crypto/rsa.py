from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64

class RSAEncryptor:
    def __init__(self, pub_key):
        self.pub_key = RSA.import_key(pub_key)
        self.cipher = PKCS1_OAEP.new(self.pub_key)
    
    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        encrypted = self.cipher.encrypt(data)
        return base64.b64encode(encrypted).decode('utf-8')