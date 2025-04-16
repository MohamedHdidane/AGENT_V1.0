from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

class AESEncryptor:
    def __init__(self, key):
        if len(key) not in [16, 24, 32]:
            raise ValueError("AES key must be 16, 24, or 32 bytes long")
        self.key = key.encode('utf-8')
    
    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        cipher = AES.new(self.key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data, AES.block_size))
        iv = cipher.iv
        return base64.b64encode(iv + ct_bytes).decode('utf-8')
    
    def decrypt(self, enc_data):
        enc_data = base64.b64decode(enc_data)
        iv = enc_data[:AES.block_size]
        ct = enc_data[AES.block_size:]
        
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return pt.decode('utf-8')