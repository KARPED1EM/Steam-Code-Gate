from typing import List, Optional

from sqlalchemy.orm import Session

from src.database.models import Administrator
from src.repositories.base import BaseRepository


class AdministratorRepository(BaseRepository[Administrator]):
    def __init__(self, db: Session):
        super().__init__(Administrator, db)

    def get_by_username(self, username: str) -> Optional[Administrator]:
        return self.db.query(Administrator).filter(Administrator.username == username).first()

    def get_all_admins(self) -> List[Administrator]:
        return self.db.query(Administrator).filter(Administrator.is_super_admin == False).all()

    def get_super_admins(self) -> List[Administrator]:
        return self.db.query(Administrator).filter(Administrator.is_super_admin == True).all()

    def username_exists(self, username: str, exclude_id: Optional[int] = None) -> bool:
        query = self.db.query(Administrator).filter(Administrator.username == username)
        if exclude_id:
            query = query.filter(Administrator.id != exclude_id)
        return query.first() is not None
