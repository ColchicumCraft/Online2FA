
# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    oid = Column(String(64), unique=True, index=True, nullable=False)
    display_name = Column(String(255))
    email = Column(String(255))
    accounts = relationship("TOTPAccount", back_populates="user", cascade="all, delete-orphan")

class TOTPAccount(Base):
    __tablename__ = "totp_accounts"
    id = Column(Integer, primary_key=True)
    user_oid = Column(String(64), ForeignKey("users.oid", ondelete="CASCADE"), index=True, nullable=False)
    account_name = Column(String(255), nullable=False)
    email = Column(String(255), default="")
    issuer = Column(String(100), default="Microsoft Azure")
    secret_encrypted = Column(Text, nullable=False)
    type = Column(String(50), default="manual")
    qr_png_path = Column(String(512), default=None)
    added_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="accounts")
