# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev")
    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == False

    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_DB = os.getenv("MYSQL_DB", "totp_app")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    )

    MSAL_CLIENT_ID = os.getenv("MSAL_CLIENT_ID")
    MSAL_CLIENT_SECRET = os.getenv("MSAL_CLIENT_SECRET")
    MSAL_TENANT_ID = os.getenv("MSAL_TENANT_ID")
    MSAL_REDIRECT_URI = os.getenv("MSAL_REDIRECT_URI", "http://localhost:5000/auth/callback")
    MSAL_AUTHORITY = f"https://login.microsoftonline.com/{MSAL_TENANT_ID}"
    MSAL_SCOPES = [s.strip() for s in os.getenv("MSAL_SCOPES", "User.Read").split() if s.strip()]

    TOTP_ENC_KEY = os.getenv("TOTP_ENC_KEY")

    SESSION_TYPE = os.getenv("SESSION_TYPE", "filesystem")
    SESSION_FILE_DIR = os.getenv("SESSION_FILE_DIR")

settings = Settings()