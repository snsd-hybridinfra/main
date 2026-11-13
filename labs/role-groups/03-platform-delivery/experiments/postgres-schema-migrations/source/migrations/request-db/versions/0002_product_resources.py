"""add product parameters and resource presentation fields

Revision ID: 0002_request_products
Revises: 0001_request
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_request_products"
down_revision: str | None = "0001_request"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "access_requests",
        sa.Column(
            "parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        schema="request_service",
    )
    op.add_column(
        "resource_projections",
        sa.Column("resource_type", sa.String(64), nullable=False, server_default="DEV-OS-VM-S"),
        schema="request_service",
    )
    op.add_column(
        "resource_projections",
        sa.Column("display_name", sa.String(255), nullable=False, server_default="할당 자원"),
        schema="request_service",
    )
    op.add_column(
        "resource_projections",
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        schema="request_service",
    )


def downgrade() -> None:
    op.drop_column("resource_projections", "details", schema="request_service")
    op.drop_column("resource_projections", "display_name", schema="request_service")
    op.drop_column("resource_projections", "resource_type", schema="request_service")
    op.drop_column("access_requests", "parameters", schema="request_service")
