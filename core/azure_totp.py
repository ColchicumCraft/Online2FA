# -*- coding: utf-8 -*-
import hmac, hashlib, time, base64, struct, qrcode
from urllib.parse import quote

class AzureTOTP:
    def __init__(self, secret_key=None):
        self.secret_key = (secret_key.upper().replace(' ', '') if secret_key else self.generate_secret_key())
        self.time_step = 30
        self.digits = 6
        self.algorithm = hashlib.sha1
    @staticmethod
    def generate_secret_key(length=20):
        import os as os_random
        return base64.b32encode(os_random.urandom(length)).decode('utf-8').replace('=', '')
    def _base32_decode(self, key):
        padding = '=' * ((8 - len(key) % 8) % 8)
        return base64.b32decode(key + padding)
    def get_totp_code(self, timestamp=None):
        timestamp = timestamp or time.time()
        counter = int(timestamp) // self.time_step
        msg = struct.pack('>Q', counter)
        key = self._base32_decode(self.secret_key)
        h = hmac.new(key, msg, self.algorithm).digest()
        offset = h[-1] & 0x0F
        val = struct.unpack('>I', h[offset:offset+4])[0] & 0x7FFFFFFF
        return str(val % (10**self.digits)).zfill(self.digits)
    def verify_code(self, code, timestamp=None, valid_window=1):
        timestamp = timestamp or time.time()
        for i in range(-valid_window, valid_window+1):
            if self.get_totp_code(timestamp + i*self.time_step) == str(code).zfill(self.digits):
                return True
        return False

def build_otpauth_uri(secret, email, issuer_name='Microsoft Azure'):
    label = f"{issuer_name}:{email}"
    params = [f"secret={secret}", f"issuer={quote(issuer_name)}", "algorithm=SHA1", "digits=6", "period=30"]
    return f"otpauth://totp/{quote(label)}?{'&'.join(params)}"

def generate_qr_image(uri):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=2)
    qr.add_data(uri); qr.make(fit=True)
    return qr.make_image(fill_color='black', back_color='white')