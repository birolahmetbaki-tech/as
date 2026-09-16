"""Veritabani baglantisi ve oturum yonetimi."""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app import config


class Base(DeclarativeBase):
    pass


def _create_engine():
    url = config.database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, future=True)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_connection, _record):
            cursor = dbapi_connection.cursor()
            # WAL: yazma sirasinda okuma yapilabilir ve cokmeye karsi dayanikli.
            cursor.execute("PRAGMA journal_mode=WAL")
            # Foreign key kisitlari SQLite'ta varsayilan olarak kapalidir.
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
