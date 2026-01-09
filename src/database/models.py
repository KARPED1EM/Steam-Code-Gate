from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.constants import CodeProviderType
from src.database.connection import Base


class Administrator(Base):
    __tablename__ = "administrators"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    contact_info = Column(Text, nullable=True)
    is_super_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    steam_accounts = relationship("SteamAccount", back_populates="owner", cascade="all, delete-orphan")


class SteamAccount(Base):
    __tablename__ = "steam_accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    account_name = Column(String(100), nullable=False)
    password = Column(String(128), nullable=True)
    is_password_public = Column(Boolean, default=False, nullable=False)
    code_provider_type = Column(Enum(CodeProviderType), nullable=False, index=True)
    email_config = Column(Text, nullable=True)
    otp_token = Column(String(255), nullable=True)
    access_passphrase = Column(String(128), nullable=False, index=True)
    latest_code = Column(String(10), nullable=True)
    latest_code_updated_at = Column(DateTime, nullable=True)
    latest_email_code_at = Column(DateTime, nullable=True)
    owner_id = Column(Integer, ForeignKey("administrators.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("Administrator", back_populates="steam_accounts")
