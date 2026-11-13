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
    with engine.begin() as connection:
        inspector = inspect(connection)
        if inspector.has_table("approval_requests"):
            existing = {
                column["name"] for column in inspector.get_columns("approval_requests")
            }
            if "parameters" not in existing:
                connection.execute(
                    text("ALTER TABLE approval_requests ADD COLUMN parameters JSON NOT NULL DEFAULT '{}'")
                )

        if inspector.has_table("provisioning_jobs"):
            job_columns = {
                column["name"] for column in inspector.get_columns("provisioning_jobs")
            }
            additions = {
                "product_version": "INTEGER NOT NULL DEFAULT 1",
                "artifact_digest": "VARCHAR(80) NOT NULL DEFAULT ''",
                "approved_by": "VARCHAR(255) NOT NULL DEFAULT 'legacy-approver'",
                "expires_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
            }
            for name, definition in additions.items():
                if name not in job_columns:
                    connection.execute(
                        text(f"ALTER TABLE provisioning_jobs ADD COLUMN {name} {definition}")
                    )


def get_db(request: Request) -> Generator[Session, None, None]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()
