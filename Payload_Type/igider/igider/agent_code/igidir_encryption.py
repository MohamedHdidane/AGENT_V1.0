import base64
import os
from typing import Tuple, Union
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key

class EncryptionModule:
    def __init__(self):
        # For a real agent, you would have hardcoded keys or fetch them at runtime
        # For demo purposes, we'll generate them dynamically
        self.session_key = os.urandom(32)  # AES-256 key
        self.aes_iv_size = 16  # AES block size for IV
    
    def generate_keys(self) -> Tuple[bytes, bytes]:
        """Generate RSA key pair for secure key exchange"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    def encrypt(self, data: str) -> str:
        """Encrypt data using AES-256-CBC with the session key"""
        # Generate a random IV
        iv = os.urandom(self.aes_iv_size)
        
        # Pad the data to the block size
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(data.encode()) + padder.finalize()
        
        # Create the cipher
        cipher = Cipher(
            algorithms.AES(self.session_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Encrypt the data
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine IV and encrypted data, then encode to base64
        result = base64.b64encode(iv + encrypted_data).decode()
        return result
    
    def decrypt(self, data: str) -> str:
        """Decrypt data using AES-256-CBC with the session key"""
        # Decode from base64
        raw_data = base64.b64decode(data.encode())
        
        # Extract IV and encrypted data
        iv = raw_data[:self.aes_iv_size]
        encrypted_data = raw_data[self.aes_iv_size:]
        
        # Create the cipher
        cipher = Cipher(
            algorithms.AES(self.session_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt the data
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Unpad the data
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data.decode()
    
    def encrypt_with_public_key(self, data: str, public_key_pem: bytes) -> str:
        """Encrypt data using an RSA public key"""
        public_key = load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )
        
        encrypted_data = public_key.encrypt(
            data.encode(),
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_with_private_key(self, data: str, private_key_pem: bytes, password: bytes = None) -> str:
        """Decrypt data using an RSA private key"""
        encrypted_data = base64.b64decode(data.encode())
        
        private_key = load_pem_private_key(
            private_key_pem,
            password=password,
            backend=default_backend()
        )
        
        decrypted_data = private_key.decrypt(
            encrypted_data,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return decrypted_data.decode()
    
    def derive_key_from_password(self, password: str, salt: bytes = None) -> bytes:
        """Derive a symmetric key from a password"""
        if salt is None:
            salt = os.urandom(16)
            
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode())
        return key, salt
    
    def compute_hmac(self, data: str, key: bytes = None) -> str:
        """Compute HMAC for data integrity verification"""
        if key is None:
            key = self.session_key
            
        from cryptography.hazmat.primitives import hmac
        
        h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
        h.update(data.encode())
        signature = h.finalize()
        
        return base64.b64encode(signature).decode()
    
    def verify_hmac(self, data: str, signature: str, key: bytes = None) -> bool:
        """Verify HMAC signature"""
        if key is None:
            key = self.session_key
            
        from cryptography.hazmat.primitives import hmac
        
        h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
        h.update(data.encode())
        
        try:
            h.verify(base64.b64decode(signature.encode()))
            return True
        except Exception:
            return False