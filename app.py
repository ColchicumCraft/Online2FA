
# -*- coding: utf-8 -*-
from flask import Flask, redirect, url_for, session
from flask_session import Session
from sqlalchemy import text
from config import settings
from db import Base, engine

# ✅ 关键：显式导入 models，确保 Base 已注册所有表定义
import db.models  # noqa: F401

# 同时在函数内再导入蓝图（顺序无所谓了，models 已在此处 import）

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = settings.SECRET_KEY
    app.config['SESSION_TYPE'] = settings.SESSION_TYPE
    if settings.SESSION_FILE_DIR:
        app.config['SESSION_FILE_DIR'] = settings.SESSION_FILE_DIR
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800
    Session(app)

    # 先创建表（此时 db.models 已导入，元数据齐全）
    Base.metadata.create_all(bind=engine)

    # 尝试为旧库添加 issuer 列（MySQL 8+ 支持 IF NOT EXISTS）
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE totp_accounts ADD COLUMN IF NOT EXISTS issuer VARCHAR(100) DEFAULT 'Microsoft Azure'"))
    except Exception:
        pass

    from routes.auth import bp as auth_bp
    from routes.accounts import bp as accounts_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(accounts_bp, url_prefix="/")

    @app.route("/")
    def root():
        if session.get("user"):
            return redirect(url_for("accounts.index"))
        return redirect(url_for("auth.login"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=settings.FLASK_HOST, port=settings.FLASK_PORT, debug=settings.FLASK_DEBUG)
