from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from src.config import config
from src.constants import UserRole


def create_access_token(user_id: int, role: UserRole, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "sub": str(user_id),
        "role": role.value,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return encoded_jwt


def create_guest_token(passphrase: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=8)
    to_encode = {
        "passphrase": passphrase,
        "role": UserRole.GUEST.value,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
