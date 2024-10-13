import hashlib
import os
from cryptography.fernet import Fernet

# Generate a key for encryption (in a real-world scenario, this should be stored securely)
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

def hash_password(password):
    """Hash a password for storing."""
    salt = os.urandom(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt + pwdhash

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:32]
    stored_pwdhash = stored_password[32:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return pwdhash == stored_pwdhash

def encrypt_password(password):
    """Encrypt a password for storing."""
    return cipher_suite.encrypt(password.encode())

def decrypt_password(encrypted_password):
    """Decrypt a stored password."""
    return cipher_suite.decrypt(encrypted_password).decode()

