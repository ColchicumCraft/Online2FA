# -*- coding: utf-8 -*-
from cryptography.fernet import Fernet
from config import settings
if not settings.TOTP_ENC_KEY:
    raise RuntimeError("TOTP_ENC_KEY 未配置，请在 .env 中配置 Fernet 密钥")
fernet = Fernet(settings.TOTP_ENC_KEY.encode())

def encrypt_secret(plain: str) -> str:
    return fernet.encrypt(plain.encode()).decode()

def decrypt_secret(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()