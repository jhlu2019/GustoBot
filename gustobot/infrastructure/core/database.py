"""
Database configuration helpers and session utilities.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Generator, Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from gustobot.config import settings

_DEFAULT_LOG_ECHO = bool(settings.DEBUG)

_connect_args: Dict[str, bool] = {}
if settings.DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=_DEFAULT_LOG_ECHO,
    future=True,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)

Base = declarative_base()


def init_db(*, create_all: bool = False) -> None:
    """
    Initialize the database engine.

    If `create_all` is True the metadata for all models is created.
    """
    if create_all:
        # Lazy import to avoid circular dependencies during startup.
        import gustobot.infrastructure.persistence.db.models  # noqa: F401

        Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session dependency for FastAPI routes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope(*, commit: bool = True) -> Iterator[Session]:
    """
    Context manager that handles commit/rollback automatically.
    """
    session = SessionLocal()
    try:
        yield session
        if commit:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
