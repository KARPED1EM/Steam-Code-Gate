from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.constants import Validation


class AdministratorBase(BaseModel):
    username: str = Field(..., min_length=Validation.MIN_USERNAME_LENGTH, max_length=Validation.MAX_USERNAME_LENGTH)
    contact_info: Optional[str] = Field(None, max_length=Validation.MAX_CONTACT_INFO_LENGTH)


class AdministratorCreate(AdministratorBase):
    password: str = Field(..., min_length=Validation.MIN_PASSWORD_LENGTH, max_length=Validation.MAX_PASSWORD_LENGTH)
    is_super_admin: bool = False


class AdministratorUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=Validation.MIN_USERNAME_LENGTH, max_length=Validation.MAX_USERNAME_LENGTH)
    password: Optional[str] = Field(None, min_length=Validation.MIN_PASSWORD_LENGTH, max_length=Validation.MAX_PASSWORD_LENGTH)
    contact_info: Optional[str] = Field(None, max_length=Validation.MAX_CONTACT_INFO_LENGTH)


class AdministratorResponse(AdministratorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_super_admin: bool
    created_at: datetime
    updated_at: datetime


class AdministratorLogin(BaseModel):
    username: str
    password: str
