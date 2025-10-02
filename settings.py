import os

def _default_host_for_username(username: str) -> str:
    u = (username or "").lower()
    if u.endswith("@qq.com"):
        return "imap.qq.com"
    if u.endswith("@gmail.com"):
        return "imap.gmail.com"
    if u.endswith("@outlook.com") or u.endswith("@hotmail.com") or u.endswith("@live.com"):
        return "imap.outlook.com"
    return "imap.qq.com"

class Settings:
    # Host default auto-detects by username domain; can be overridden by env
    IMAP_USERNAME = os.getenv("IMAP_USERNAME", "")
    IMAP_HOST = os.getenv("IMAP_HOST", _default_host_for_username(IMAP_USERNAME))
    IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))

    # IMPORTANT: provide via environment variable in production
    IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")

    # Steam sender (comma-separated to support multiple if needed)
    SENDER_FILTER = os.getenv("SENDER_FILTER", "noreply@steampowered.com")

    DEBUG = os.getenv("DEBUG", "0") == "1"