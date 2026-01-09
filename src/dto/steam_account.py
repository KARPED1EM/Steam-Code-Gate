from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.constants import CodeProviderType, Validation


class EmailConfig(BaseModel):
    imap_server: str
    imap_port: int
    email_address: str
    email_password: str
    use_ssl: bool = True


class SteamAccountBase(BaseModel):
    name: str = Field(..., max_length=Validation.MAX_STEAM_ACCOUNT_NAME_LENGTH)
    account_name: str = Field(..., max_length=Validation.MAX_STEAM_ACCOUNT_USERNAME_LENGTH)
    code_provider_type: CodeProviderType


class SteamAccountCreate(SteamAccountBase):
    password: Optional[str] = Field(None, max_length=Validation.MAX_STEAM_PASSWORD_LENGTH)
    is_password_public: bool = False
    email_config: Optional[EmailConfig] = None
    otp_token: Optional[str] = None
    access_passphrase: str = Field(..., max_length=Validation.MAX_PASSPHRASE_LENGTH)


class SteamAccountUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=Validation.MAX_STEAM_ACCOUNT_NAME_LENGTH)
    account_name: Optional[str] = Field(None, max_length=Validation.MAX_STEAM_ACCOUNT_USERNAME_LENGTH)
    password: Optional[str] = Field(None, max_length=Validation.MAX_STEAM_PASSWORD_LENGTH)
    is_password_public: Optional[bool] = None
    code_provider_type: Optional[CodeProviderType] = None
    email_config: Optional[EmailConfig] = None
    otp_token: Optional[str] = None
    access_passphrase: Optional[str] = Field(None, max_length=Validation.MAX_PASSPHRASE_LENGTH)


class SteamAccountResponse(SteamAccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    password: Optional[str] = None
    is_password_public: bool
    latest_code: Optional[str] = None
    latest_code_updated_at: Optional[datetime] = None
    owner_id: int
    created_at: datetime
    updated_at: datetime


class SteamAccountDetailResponse(SteamAccountResponse):
    email_config: Optional[str] = None
    otp_token: Optional[str] = None
    access_passphrase: str


class SteamAccountGuestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    account_name: str
    password: Optional[str] = None
    code_provider_type: CodeProviderType


class OwnerContactResponse(BaseModel):
    contact_info: Optional[str] = None
