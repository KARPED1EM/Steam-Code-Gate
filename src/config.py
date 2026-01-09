import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from src.constants import JWT


_DOTENV_LOADED = False


def _load_dotenv_once(base_dir: Path) -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    candidates = [base_dir / ".env", base_dir / "src" / ".env"]
    for path in candidates:
        if path.exists():
            load_dotenv(dotenv_path=path, override=False)
            break
    _DOTENV_LOADED = True


class Config:
    def __init__(self) -> None:
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATABASE_PATH = self._get_required_env("DATABASE_PATH")
        self.JWT_SECRET_KEY = self._get_required_env("JWT_SECRET_KEY")
        self.JWT_ALGORITHM = JWT.ALGORITHM
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = JWT.ACCESS_TOKEN_EXPIRE_MINUTES

        self.TEMPLATES_DIR = str(self.BASE_DIR / "src" / "templates")
        self.STATIC_DIR = str(self.BASE_DIR / "src" / "static")

        self._validate_database_path()

    def _get_required_env(self, name: str) -> str:
        value = os.getenv(name)
        if value is None or not value.strip():
            _load_dotenv_once(self.BASE_DIR)
            value = os.getenv(name)
        if value is None or not value.strip():
            raise RuntimeError(f"Missing required environment variable: {name}")
        return value.strip()

    def _validate_database_path(self) -> None:
        db_path = Path(self.DATABASE_PATH).expanduser()
        if db_path.exists() and db_path.is_dir():
            raise RuntimeError("DATABASE_PATH must point to a file, not a directory.")
        parent_dir = db_path.parent
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
        self.DATABASE_PATH = str(db_path)


config = Config()
