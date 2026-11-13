from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def ensure_local_schema_compatibility(engine: Engine) -> None:
    definitions = {
        "access_requests": {"parameters": "JSON NOT NULL DEFAULT '{}'"},
        "resource_projections": {
            "resource_type": "VARCHAR(64) NOT NULL DEFAULT 'DEV-OS-VM-S'",
            "display_name": "VARCHAR(255) NOT NULL DEFAULT '할당 자원'",
            "details": "JSON NOT NULL DEFAULT '{}'",
        },
    }
    with engine.begin() as connection:
        inspector = inspect(connection)
        for table_name, columns in definitions.items():
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, ddl in columns.items():
                if column_name not in existing:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))


def get_db(request: Request) -> Generator[Session, None, None]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()
