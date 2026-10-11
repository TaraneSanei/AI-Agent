import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from ai_agent.config import Settings
from ai_agent.database import create_database_engine, create_session_factory, session_scope


@pytest.fixture
def engine(tmp_path):
    settings = Settings(
        _env_file=None,
        app_env="development",
        database_url=f"sqlite+pysqlite:///{tmp_path / 'data' / 'test.db'}",
    )
    database = create_database_engine(settings)
    yield database
    database.dispose()


def test_transactions_commit_and_rollback(engine):
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY)"))
    factory = create_session_factory(engine)

    with session_scope(factory) as session:
        session.execute(text("INSERT INTO items VALUES (1)"))

    with pytest.raises(RuntimeError), session_scope(factory) as session:
        session.execute(text("INSERT INTO items VALUES (2)"))
        raise RuntimeError("Abort the transaction")

    with engine.connect() as connection:
        assert connection.execute(text("SELECT id FROM items")).scalars().all() == [1]


def test_sqlite_enforces_foreign_keys(engine):
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE parents (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE children (parent_id INTEGER REFERENCES parents(id))"))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(text("INSERT INTO children VALUES (99)"))


def test_production_rejects_sqlite():
    with pytest.raises(ValidationError, match="postgresql\\+psycopg"):
        Settings(_env_file=None, app_env="production", database_url="sqlite:///:memory:")


def test_postgresql_driver_is_configured_without_connecting():
    settings = Settings(
        _env_file=None,
        app_env="production",
        database_url="postgresql+psycopg://user:password@localhost/ai_agent",
    )
    database = create_database_engine(settings)
    try:
        assert database.dialect.name == "postgresql"
        assert database.dialect.driver == "psycopg"
    finally:
        database.dispose()
