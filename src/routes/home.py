import json
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.config import config
from src.constants import CodeProviderType, EmailDebounce
from src.database.connection import get_db
from src.database.models import SteamAccount
from src.dto.steam_account import OwnerContactResponse, SteamAccountGuestResponse
from src.repositories.steam_account import SteamAccountRepository
from src.services.auth import AuthContext, get_current_user
from src.services.code_provider.email_provider import EmailProvider
from src.services.code_provider.otp_provider import OTPProvider

router = APIRouter()
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)


def get_accessible_accounts(auth: AuthContext, db: Session) -> List[SteamAccount]:
    repo = SteamAccountRepository(db)

    if auth.is_guest:
        return repo.get_by_passphrase(auth.passphrase)
    elif auth.is_super_admin:
        return repo.get_all()
    elif auth.is_admin:
        return repo.get_by_owner(auth.user_id)

    return []


def prepare_account_response(account: SteamAccount) -> dict:
    response = SteamAccountGuestResponse.model_validate(account).model_dump()

    if not account.is_password_public:
        response["password"] = "密码未公开"

    return response


def format_email_timestamp(value):
    if not value:
        return None
    return value.replace(tzinfo=timezone.utc).isoformat()


@router.get("/home", response_class=HTMLResponse)
async def home_page(
    request: Request,
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    accounts = get_accessible_accounts(auth, db)
    accounts_data = [prepare_account_response(acc) for acc in accounts]

    return templates.TemplateResponse("home.html", {
        "request": request,
        "accounts": accounts_data,
        "is_guest": auth.is_guest,
        "is_admin": auth.is_admin
    })


@router.get("/api/account/{account_id}/code")
async def get_verification_code(
    account_id: int,
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    repo = SteamAccountRepository(db)
    account = repo.get_by_id(account_id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    accessible_accounts = get_accessible_accounts(auth, db)
    if account not in accessible_accounts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if account.code_provider_type == CodeProviderType.OTP:
        provider = OTPProvider(account.otp_token)
        code = provider.get_code()
        remaining = provider.get_remaining_seconds()

        repo.update_latest_code(account_id, code)

        return {
            "code": code,
            "remaining_seconds": remaining,
            "provider_type": "otp"
        }
    else:
        now = datetime.utcnow()
        if account.latest_code and account.latest_code_updated_at:
            age_seconds = (now - account.latest_code_updated_at).total_seconds()
            if age_seconds < EmailDebounce.SECONDS:
                return {
                    "code": account.latest_code,
                    "remaining_seconds": None,
                    "provider_type": "email",
                    "code_timestamp": format_email_timestamp(account.latest_email_code_at)
                }

        email_config = json.loads(account.email_config)
        provider = EmailProvider(
            imap_server=email_config["imap_server"],
            imap_port=email_config["imap_port"],
            email_address=email_config["email_address"],
            email_password=email_config["email_password"],
            use_ssl=email_config.get("use_ssl", True)
        )
        result = provider.fetch_latest_code_since(account.latest_email_code_at)

        if result and result.code:
            repo.update_latest_code(account_id, result.code, code_time=result.code_timestamp)
            return {
                "code": result.code,
                "remaining_seconds": None,
                "provider_type": "email",
                "code_timestamp": format_email_timestamp(result.code_timestamp)
            }

        if account.latest_code:
            repo.touch_latest_code_timestamp(account_id)
            return {
                "code": account.latest_code,
                "remaining_seconds": None,
                "provider_type": "email",
                "code_timestamp": format_email_timestamp(account.latest_email_code_at)
            }

        return {
            "code": None,
            "remaining_seconds": None,
            "provider_type": "email",
            "code_timestamp": None
        }


@router.get("/api/account/{account_id}/contact")
async def get_owner_contact(
    account_id: int,
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    repo = SteamAccountRepository(db)
    account = repo.get_by_id(account_id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    accessible_accounts = get_accessible_accounts(auth, db)
    if account not in accessible_accounts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return OwnerContactResponse(contact_info=account.owner.contact_info)
