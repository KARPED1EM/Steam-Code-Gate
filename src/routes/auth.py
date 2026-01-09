from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.config import config
from src.constants import UserRole
from src.database.connection import get_db
from src.repositories.administrator import AdministratorRepository
from src.repositories.steam_account import SteamAccountRepository
from src.services.password import verify_password
from src.services.session import create_access_token, create_guest_token

router = APIRouter()
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login/guest")
async def guest_login(
    passphrase: str = Form(...),
    db: Session = Depends(get_db)
):
    repo = SteamAccountRepository(db)
    accounts = repo.get_by_passphrase(passphrase)

    if not accounts:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "无效的访问口令"}
        )

    token = create_guest_token(passphrase)
    response = RedirectResponse(url="/home", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


@router.post("/login/admin")
async def admin_login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    repo = AdministratorRepository(db)
    admin = repo.get_by_username(username)

    if not admin or not verify_password(password, admin.password_hash):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "用户名或密码错误"}
        )

    role = UserRole.SUPER_ADMIN if admin.is_super_admin else UserRole.ADMIN
    token = create_access_token(admin.id, role)

    response = RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response
