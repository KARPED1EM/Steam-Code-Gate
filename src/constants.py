from enum import Enum


class CodeProviderType(str, Enum):
    EMAIL = "email"
    OTP = "otp"


class UserRole(str, Enum):
    GUEST = "guest"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class SteamTOTP:
    ALPHABET = "23456789BCDFGHJKMNPQRTVWXY"
    TIME_STEP = 30
    CODE_LENGTH = 5


class EmailDebounce:
    SECONDS = 15


class JWT:
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7


class Database:
    DEFAULT_PATH = "scg.db"


class Validation:
    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 50
    MIN_PASSWORD_LENGTH = 6
    MAX_PASSWORD_LENGTH = 128
    MAX_CONTACT_INFO_LENGTH = 500
    MAX_STEAM_ACCOUNT_NAME_LENGTH = 100
    MAX_STEAM_ACCOUNT_USERNAME_LENGTH = 100
    MAX_STEAM_PASSWORD_LENGTH = 128
    MAX_PASSPHRASE_LENGTH = 128
