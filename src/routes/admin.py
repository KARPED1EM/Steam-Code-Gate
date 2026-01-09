import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.config import config
from src.constants import CodeProviderType
from src.database.connection import get_db
from src.database.models import Administrator, SteamAccount
from src.dto.administrator import AdministratorCreate, AdministratorResponse, AdministratorUpdate
from src.dto.steam_account import (
    SteamAccountCreate,
    SteamAccountDetailResponse,
    SteamAccountUpdate
)
from src.repositories.administrator import AdministratorRepository
from src.repositories.steam_account import SteamAccountRepository
from src.services.auth import AuthContext, get_administrator, require_admin, require_super_admin
from src.services.code_provider.email_provider import EmailProvider
from src.services.password import hash_password

router = APIRouter()
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(
    request: Request,
    auth: AuthContext = Depends(require_admin),
    admin: Administrator = Depends(get_administrator),
    db: Session = Depends(get_db)
):
    steam_repo = SteamAccountRepository(db)
    my_accounts = steam_repo.get_by_owner(auth.user_id)

    other_accounts = []
    all_admins = []

    if auth.is_super_admin:
        other_accounts = steam_repo.get_all_except_owner(auth.user_id)
        admin_repo = AdministratorRepository(db)
        all_admins = admin_repo.get_all()

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "admin": admin,
        "my_accounts": my_accounts,
        "other_accounts": other_accounts,
        "all_admins": all_admins,
        "is_super_admin": auth.is_super_admin
    })


@router.get("/api/admin/profile", response_model=AdministratorResponse)
async def get_profile(admin: Administrator = Depends(get_administrator)):
    return AdministratorResponse.model_validate(admin)


@router.put("/api/admin/profile")
async def update_profile(
    update_data: AdministratorUpdate,
    auth: AuthContext = Depends(require_admin),
    admin: Administrator = Depends(get_administrator),
    db: Session = Depends(get_db)
):
    repo = AdministratorRepository(db)

    if update_data.username is not None:
        if repo.username_exists(update_data.username, exclude_id=admin.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        admin.username = update_data.username

    if update_data.password is not None:
        admin.password_hash = hash_password(update_data.password)

    if update_data.contact_info is not None:
        admin.contact_info = update_data.contact_info

    repo.update(admin)
    return {"message": "Profile updated successfully"}


@router.get("/api/admin/steam-accounts", response_model=List[SteamAccountDetailResponse])
async def list_my_steam_accounts(
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db)
):
    repo = SteamAccountRepository(db)
    accounts = repo.get_by_owner(auth.user_id)
    return [SteamAccountDetailResponse.model_validate(acc) for acc in accounts]


@router.get("/api/admin/steam-accounts/email-status")
async def get_email_service_status(
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db)
):
    repo = SteamAccountRepository(db)
    accounts = repo.get_all() if auth.is_super_admin else repo.get_by_owner(auth.user_id)
    statuses = []

    for account in accounts:
        if account.code_provider_type != CodeProviderType.EMAIL or not account.email_config:
            continue

        email_config = json.loads(account.email_config)
        provider = EmailProvider(
            imap_server=email_config["imap_server"],
            imap_port=email_config["imap_port"],
            email_address=email_config["email_address"],
            email_password=email_config["email_password"],
            use_ssl=email_config.get("use_ssl", True)
        )
        is_ok, detail = provider.check_health()
        statuses.append({
            "account_id": account.id,
            "status": "ok" if is_ok else "error",
            "detail": detail
        })

    return {"statuses": statuses}


@router.post("/api/admin/steam-accounts")
async def create_steam_account(
    account_data: SteamAccountCreate,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db)
):
    repo = SteamAccountRepository(db)

    if account_data.password and not account_data.is_password_public:
        account_data.is_password_public = False
    elif not account_data.password:
        account_data.is_password_public = False

    if account_data.code_provider_type == CodeProviderType.EMAIL:
        if not account_data.email_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email config is required for email provider"
            )
        email_config_str = json.dumps(account_data.email_config.model_dump())
        if repo.email_config_exists(email_config_str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email configuration already exists for another account"
            )
    elif account_data.code_provider_type == CodeProviderType.OTP:
        if not account_data.otp_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP token is required for OTP provider"
            )

    new_account = SteamAccount(
        name=account_data.name,
        account_name=account_data.account_name,
        password=account_data.password,
        is_password_public=account_data.is_password_public,
        code_provider_type=account_data.code_provider_type,
        email_config=json.dumps(account_data.email_config.model_dump()) if account_data.email_config else None,
        otp_token=account_data.otp_token,
        access_passphrase=account_data.access_passphrase,
        owner_id=auth.user_id
    )

    created = repo.create(new_account)
    return {"message": "Steam account created successfully", "id": created.id}


@router.put("/api/admin/steam-accounts/{account_id}")
async def update_steam_account(
    account_id: int,
    update_data: SteamAccountUpdate,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db)
):
    repo = SteamAccountRepository(db)
    account = repo.get_by_id(account_id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    if account.owner_id != auth.user_id and not auth.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if update_data.name is not None:
        account.name = update_data.name

    if update_data.account_name is not None:
        account.account_name = update_data.account_name

    if update_data.password is not None:
        account.password = update_data.password

    if update_data.is_password_public is not None:
        if not account.password:
            account.is_password_public = False
        else:
            account.is_password_public = update_data.is_password_public

    if update_data.code_provider_type is not None:
        account.code_provider_type = update_data.code_provider_type

    if update_data.email_config is not None:
        email_config_str = json.dumps(update_data.email_config.model_dump())
        if repo.email_config_exists(email_config_str, exclude_id=account_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email configuration already exists for another account"
            )
        account.email_config = email_config_str

    if update_data.otp_token is not None:
        account.otp_token = update_data.otp_token

    if update_data.access_passphrase is not None:
        account.access_passphrase = update_data.access_passphrase

    repo.update(account)
    return {"message": "Steam account updated successfully"}


@router.delete("/api/admin/steam-accounts/{account_id}")
async def delete_steam_account(
    account_id: int,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db)
):
    repo = SteamAccountRepository(db)
    account = repo.get_by_id(account_id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    if account.owner_id != auth.user_id and not auth.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    repo.delete(account)
    return {"message": "Steam account deleted successfully"}


@router.get("/api/super-admin/steam-accounts", response_model=List[SteamAccountDetailResponse])
async def list_all_steam_accounts(
    owner_id: Optional[int] = None,
    auth: AuthContext = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    repo = SteamAccountRepository(db)

    if owner_id:
        accounts = repo.get_by_owner(owner_id)
    else:
        accounts = repo.get_all()

    return [SteamAccountDetailResponse.model_validate(acc) for acc in accounts]


@router.put("/api/super-admin/steam-accounts/{account_id}/transfer")
async def transfer_account_ownership(
    account_id: int,
    new_owner_id: int,
    auth: AuthContext = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    steam_repo = SteamAccountRepository(db)
    admin_repo = AdministratorRepository(db)

    account = steam_repo.get_by_id(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    new_owner = admin_repo.get_by_id(new_owner_id)
    if not new_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="New owner not found"
        )

    account.owner_id = new_owner_id
    steam_repo.update(account)

    return {"message": "Account ownership transferred successfully"}


@router.get("/api/super-admin/administrators", response_model=List[AdministratorResponse])
async def list_administrators(
    auth: AuthContext = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    repo = AdministratorRepository(db)
    admins = repo.get_all()
    return [AdministratorResponse.model_validate(admin) for admin in admins]


@router.post("/api/super-admin/administrators")
async def create_administrator(
    admin_data: AdministratorCreate,
    auth: AuthContext = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    repo = AdministratorRepository(db)

    if repo.username_exists(admin_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    new_admin = Administrator(
        username=admin_data.username,
        password_hash=hash_password(admin_data.password),
        contact_info=admin_data.contact_info,
        is_super_admin=admin_data.is_super_admin
    )

    created = repo.create(new_admin)
    return {"message": "Administrator created successfully", "id": created.id}


@router.delete("/api/super-admin/administrators/{admin_id}")
async def delete_administrator(
    admin_id: int,
    auth: AuthContext = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    if admin_id == auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    repo = AdministratorRepository(db)
    admin = repo.get_by_id(admin_id)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrator not found"
        )

    repo.delete(admin)
    return {"message": "Administrator deleted successfully"}
