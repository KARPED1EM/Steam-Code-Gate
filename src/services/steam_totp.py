import base64
import hashlib
import hmac
import time

from src.constants import SteamTOTP


def generate_steam_code(shared_secret_base64: str, timestamp: int = None) -> str:
    if timestamp is None:
        timestamp = int(time.time())

    secret_bytes = base64.b32decode(shared_secret_base64, casefold=True)

    counter = timestamp // SteamTOTP.TIME_STEP

    counter_bytes = counter.to_bytes(8, byteorder="big")

    hmac_hash = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()

    offset = hmac_hash[19] & 0x0F
    p0 = hmac_hash[offset + 0] & 0x7F
    p1 = hmac_hash[offset + 1] & 0xFF
    p2 = hmac_hash[offset + 2] & 0xFF
    p3 = hmac_hash[offset + 3] & 0xFF

    full_code = (p0 << 24) | (p1 << 16) | (p2 << 8) | p3

    code = ""
    n = full_code
    for _ in range(SteamTOTP.CODE_LENGTH):
        index = n % len(SteamTOTP.ALPHABET)
        code += SteamTOTP.ALPHABET[index]
        n = n // len(SteamTOTP.ALPHABET)

    return code


def get_remaining_seconds() -> int:
    current_time = int(time.time())
    return SteamTOTP.TIME_STEP - (current_time % SteamTOTP.TIME_STEP)
