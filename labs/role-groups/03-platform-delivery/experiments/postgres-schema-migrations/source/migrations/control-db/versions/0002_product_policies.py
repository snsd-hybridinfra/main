"""add product parameters to approval requests

Revision ID: 0002_control_products
Revises: 0001_control
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_control_products"
down_revision: str | None = "0001_control"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "approval_requests",
        sa.Column(
            "parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        schema="control_service",
    )


def downgrade() -> None:
    op.drop_column("approval_requests", "parameters", schema="control_service")
