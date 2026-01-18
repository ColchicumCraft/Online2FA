
# -*- coding: utf-8 -*-
import io, os, time
from flask import render_template, request, redirect, url_for, session, jsonify, current_app, send_file
from sqlalchemy import select
from db import SessionLocal
from db.models import TOTPAccount
from utils.crypto import encrypt_secret, decrypt_secret
from core.azure_totp import AzureTOTP, build_otpauth_uri, generate_qr_image
from . import bp

def login_required(view):
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper

@bp.route("/")
@login_required
def index():
    user = session["user"]
    db = SessionLocal()
    try:
        stmt = select(TOTPAccount).where(TOTPAccount.user_oid == user["oid"]).order_by(TOTPAccount.added_at.desc())
        items = db.execute(stmt).scalars().all()
        vm = [{
            "id": it.id,
            "account_name": it.account_name,
            "email": it.email or "未设置",
            "issuer": it.issuer or "Microsoft Azure",
            "type": it.type or "未知",
            "added_at": it.added_at.strftime("%Y-%m-%d %H:%M:%S"),
            "qr_png_path": it.qr_png_path
        } for it in items]
    finally:
        db.close()
    return render_template("accounts/index.html", items=vm, user=user)

@bp.route("/api/current_code/<int:account_id>")
@login_required
def api_current_code(account_id):
    user_oid = session["user"]["oid"]
    db = SessionLocal()
    try:
        it = db.get(TOTPAccount, account_id)
        if not it or it.user_oid != user_oid:
            return jsonify({"error": "not found"}), 404
        secret = decrypt_secret(it.secret_encrypted)
        totp = AzureTOTP(secret)
        code = totp.get_totp_code()
        time_left = 30 - (int(time.time()) % 30)
        return jsonify({"code": code, "time_left": time_left})
    finally:
        db.close()

@bp.route("/add", methods=["POST"])
@login_required
def add():
    user = session["user"]
    data = request.form
    account_name = data.get("account_name", "").strip()
    email = data.get("email", "").strip()
    issuer = data.get("issuer", "Microsoft Azure").strip() or "Microsoft Azure"
    mode = data.get("mode", "manual")
    secret = data.get("secret", "").strip().upper().replace(" ", "")
    if not account_name:
        return jsonify({"error": "账户名称不能为空"}), 400
    db = SessionLocal()
    try:
        if mode == "generated":
            secret = AzureTOTP().secret_key
        elif not secret:
            return jsonify({"error": "密钥不能为空"}), 400
        AzureTOTP(secret).get_totp_code()
        uri = build_otpauth_uri(secret, email or user["email"], issuer_name=issuer)
        img = generate_qr_image(uri)
        qrc_dir = os.path.join(current_app.root_path, "static", "qrcodes")
        os.makedirs(qrc_dir, exist_ok=True)
        fn = f"qr_{user['oid']}_{int(time.time())}.png"
        fp = os.path.join(qrc_dir, fn)
        img.save(fp)
        rec = TOTPAccount(
            user_oid=user["oid"], account_name=account_name, email=email,
            issuer=issuer, type=mode, secret_encrypted=encrypt_secret(secret),
            qr_png_path=f"/static/qrcodes/{fn}"
        )
        db.add(rec)
        db.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback(); return jsonify({"error": str(e)}), 400
    finally:
        db.close()

@bp.route("/edit/<int:account_id>", methods=["POST"])
@login_required
def edit(account_id):
    user_oid = session["user"]["oid"]
    data = request.form
    account_name = data.get("account_name", "").strip()
    email = data.get("email", "").strip()
    db = SessionLocal()
    try:
        it = db.get(TOTPAccount, account_id)
        if not it or it.user_oid != user_oid:
            return jsonify({"error": "not found"}), 404
        if account_name:
            it.account_name = account_name
            it.email = email
            db.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback(); return jsonify({"error": str(e)}), 400
    finally:
        db.close()

@bp.route("/delete/<int:account_id>", methods=["POST"])
@login_required
def delete(account_id):
    user_oid = session["user"]["oid"]
    db = SessionLocal()
    try:
        it = db.get(TOTPAccount, account_id)
        if not it or it.user_oid != user_oid:
            return jsonify({"error": "not found"}), 404
        db.delete(it); db.commit(); return jsonify({"ok": True})
    except Exception as e:
        db.rollback(); return jsonify({"error": str(e)}), 400
    finally:
        db.close()

@bp.route("/reveal/<int:account_id>")
@login_required
def reveal(account_id):
    user_oid = session["user"]["oid"]
    db = SessionLocal()
    try:
        it = db.get(TOTPAccount, account_id)
        if not it or it.user_oid != user_oid:
            return jsonify({"error": "not found"}), 404
        secret = decrypt_secret(it.secret_encrypted)
        return jsonify({"secret": secret, "issuer": it.issuer or "Microsoft Azure", "email": it.email or ""})
    finally:
        db.close()

@bp.route("/qr/<int:account_id>")
@login_required
def qr(account_id):
    user_oid = session["user"]["oid"]
    db = SessionLocal()
    try:
        it = db.get(TOTPAccount, account_id)
        if not it or it.user_oid != user_oid:
            return "not found", 404
        secret = decrypt_secret(it.secret_encrypted)
        uri = build_otpauth_uri(secret, it.email or "", issuer_name=(it.issuer or "Microsoft Azure"))
        img = generate_qr_image(uri)
        bio = io.BytesIO(); img.save(bio, format='PNG'); bio.seek(0)
        return send_file(bio, mimetype='image/png')
    finally:
        db.close()
