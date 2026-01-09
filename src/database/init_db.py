from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database.connection import Base, engine, SessionLocal
from src.database.models import Administrator


def init_database():
    Base.metadata.create_all(bind=engine)


def ensure_schema():
    with engine.begin() as connection:
        result = connection.execute(text("PRAGMA table_info(steam_accounts)")).fetchall()
        columns = {row[1] for row in result}
        if "latest_email_code_at" not in columns:
            connection.execute(
                text("ALTER TABLE steam_accounts ADD COLUMN latest_email_code_at DATETIME")
            )


def create_default_super_admin(db: Session, username: str, password_hash: str):
    existing = db.query(Administrator).filter(Administrator.username == username).first()
    if not existing:
        super_admin = Administrator(
            username=username,
            password_hash=password_hash,
            is_super_admin=True,
            contact_info=None
        )
        db.add(super_admin)
        db.commit()
        return super_admin
    return existing


def setup_database():
    init_database()
    ensure_schema()
    db = SessionLocal()
    try:
        from src.services.password import hash_password
        create_default_super_admin(db, "admin", hash_password("admin123"))
    finally:
        db.close()
