from typing import Optional

from src.services.code_provider.base import CodeProvider
from src.services.steam_totp import generate_steam_code, get_remaining_seconds


class OTPProvider(CodeProvider):
    def __init__(self, otp_token: str):
        self.otp_token = otp_token

    def get_code(self) -> Optional[str]:
        try:
            return generate_steam_code(self.otp_token)
        except Exception:
            return None

    def get_remaining_seconds(self) -> Optional[int]:
        return get_remaining_seconds()
