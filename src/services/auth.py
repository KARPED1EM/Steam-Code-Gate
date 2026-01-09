from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.constants import UserRole
from src.database.connection import get_db
from src.database.models import Administrator
from src.repositories.administrator import AdministratorRepository
from src.services.session import decode_token


class AuthContext:
    def __init__(self, user_id: Optional[int], role: UserRole, passphrase: Optional[str] = None):
        self.user_id = user_id
        self.role = role
        self.passphrase = passphrase

    @property
    def is_guest(self) -> bool:
        return self.role == UserRole.GUEST

    @property
    def is_admin(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

    @property
    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN


def get_current_user(access_token: Optional[str] = Cookie(None)) -> AuthContext:
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    payload = decode_token(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    role = UserRole(payload.get("role"))

    if role == UserRole.GUEST:
        passphrase = payload.get("passphrase")
        return AuthContext(user_id=None, role=role, passphrase=passphrase)
    else:
        user_id = int(payload.get("sub"))
        return AuthContext(user_id=user_id, role=role)


def require_admin(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
    if not auth.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return auth


def require_super_admin(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
    if not auth.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return auth


def get_administrator(auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> Administrator:
    repo = AdministratorRepository(db)
    admin = repo.get_by_id(auth.user_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrator not found"
        )
    return admin
