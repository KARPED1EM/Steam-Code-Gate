import json
from typing import List, Optional

from sqlalchemy.orm import Session

from src.constants import CodeProviderType
from src.database.models import SteamAccount
from src.repositories.base import BaseRepository


class SteamAccountRepository(BaseRepository[SteamAccount]):
    def __init__(self, db: Session):
        super().__init__(SteamAccount, db)

    def get_by_passphrase(self, passphrase: str) -> List[SteamAccount]:
        return self.db.query(SteamAccount).filter(SteamAccount.access_passphrase == passphrase).all()

    def get_by_owner(self, owner_id: int) -> List[SteamAccount]:
        return self.db.query(SteamAccount).filter(SteamAccount.owner_id == owner_id).all()

    def get_all_except_owner(self, owner_id: int) -> List[SteamAccount]:
        return self.db.query(SteamAccount).filter(SteamAccount.owner_id != owner_id).all()

    def email_config_exists(self, email_config: str, exclude_id: Optional[int] = None) -> bool:
        query = self.db.query(SteamAccount).filter(
            SteamAccount.code_provider_type == CodeProviderType.EMAIL,
            SteamAccount.email_config == email_config
        )
        if exclude_id:
            query = query.filter(SteamAccount.id != exclude_id)
        return query.first() is not None

    def update_latest_code(self, account_id: int, code: str, code_time=None, update_time=None) -> None:
        from datetime import datetime
        update_dict = {
            "latest_code": code,
            "latest_code_updated_at": update_time or datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        if code_time is not None:
            update_dict["latest_email_code_at"] = code_time

        self.db.query(SteamAccount).filter(SteamAccount.id == account_id).update(update_dict)
        self.db.commit()

    def touch_latest_code_timestamp(self, account_id: int) -> None:
        from datetime import datetime
        self.db.query(SteamAccount).filter(SteamAccount.id == account_id).update({
            "latest_code_updated_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        self.db.commit()
