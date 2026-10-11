from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.engine import Connection, Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry, StaticPool

from ai_agent.config import Settings


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


def create_database_engine(settings: Settings) -> Engine:
    url = make_url(settings.database_url.get_secret_value())
    if url.get_backend_name() != "sqlite":
        return create_engine(url, pool_pre_ping=True, hide_parameters=True)

    in_memory = url.database in {None, "", ":memory:"}
    if not in_memory:
        path = Path(url.database).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        url = url.set(database=str(path))

    options = {"poolclass": StaticPool} if in_memory else {}
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False, "timeout": 30},
        hide_parameters=True,
        **options,
    )

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection: sqlite3.Connection, _record: ConnectionPoolEntry) -> None:
        # Let SQLAlchemy manage BEGIN consistently on Python 3.11 and later.
        connection.isolation_level = None
        cursor = connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    @event.listens_for(engine, "begin")
    def begin_sqlite(connection: Connection) -> None:
        connection.exec_driver_sql("BEGIN")

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    with factory.begin() as session:
        yield session
