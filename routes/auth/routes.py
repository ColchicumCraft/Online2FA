# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, session, request, jsonify
import msal, base64, requests
from config import settings
from db import SessionLocal
from db.models import User
from . import bp

def _build_msal_app():
    return msal.ConfidentialClientApplication(
        client_id=settings.MSAL_CLIENT_ID,
        client_credential=settings.MSAL_CLIENT_SECRET,
        authority=settings.MSAL_AUTHORITY
    )

def _get_photo_data_url(access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    for url in [
        "https://graph.microsoft.com/v1.0/me/photo/$value",
        "https://graph.microsoft.com/v1.0/me/photos/64x64/$value",
        "https://graph.microsoft.com/v1.0/me/photos/96x96/$value",
    ]:
        try:
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code == 200 and r.content:
                mime = r.headers.get("Content-Type", "image/jpeg")
                b64 = base64.b64encode(r.content).decode('ascii')
                return f"data:{mime};base64,{b64}"
        except Exception:
            pass
    return None

@bp.route("/login")
def login():
    msal_app = _build_msal_app()
    auth_url = msal_app.get_authorization_request_url(
        scopes=settings.MSAL_SCOPES,
        redirect_uri=settings.MSAL_REDIRECT_URI
    )
    return redirect(auth_url)

@bp.route("/callback")
def callback():
    code = request.args.get('code')
    if not code:
        return "Login failed: no code", 400
    msal_app = _build_msal_app()
    result = msal_app.acquire_token_by_authorization_code(
        code=code,
        scopes=settings.MSAL_SCOPES,
        redirect_uri=settings.MSAL_REDIRECT_URI
    )
    if 'error' in result:
        return f"Login failed: {result.get('error_description')}", 400
    claims = result.get('id_token_claims', {})
    oid = claims.get('oid') or claims.get('sub')
    display_name = claims.get('name')
    email = claims.get('preferred_username') or claims.get('email')
    tid = claims.get('tid')
    if not oid:
        return "Login failed: no oid", 400
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.oid == oid).one_or_none()
        if not user:
            user = User(oid=oid, display_name=display_name, email=email)
            db.add(user)
        else:
            user.display_name = display_name; user.email = email
        db.commit()
    finally:
        db.close()
    photo = None
    access_token = result.get('access_token')
    if access_token:
        photo = _get_photo_data_url(access_token)
    session['user'] = { 'oid': oid, 'display_name': display_name, 'email': email, 'tid': tid, 'photo': photo }
    return redirect(url_for('accounts.index'))

@bp.route("/logout")
def logout():
    session.clear(); return redirect(url_for('auth.login'))

@bp.route("/userinfo")
def userinfo():
    return jsonify(session.get('user', {})), 200