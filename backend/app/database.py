from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_PATH = Path(__file__).resolve().parents[1] / "creditsense.db"
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def initialize_database(database_engine=engine) -> None:
    Base.metadata.create_all(bind=database_engine)
    with database_engine.begin() as connection:
        profile_columns = {
            column["name"] for column in inspect(connection).get_columns("verified_profiles")
        }
        if "user_id" not in profile_columns:
            connection.execute(
                text(
                    "ALTER TABLE verified_profiles "
                    "ADD COLUMN user_id VARCHAR(36) REFERENCES verification_users (id)"
                )
            )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_verified_profiles_user_id "
                "ON verified_profiles (user_id)"
            )
        )


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
