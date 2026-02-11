"""create_device_read_model

Revision ID: 9cee86796653
Revises: ae69bcdc89f9
Create Date: 2026-02-08 17:45:54.677024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9cee86796653'
down_revision: Union[str, Sequence[str], None] = 'ae69bcdc89f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "device_read_model",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("mac_address", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("owner_email", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_device_read_model_tenant_created_id",
        "device_read_model",
        ["tenant_id", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_device_read_model_tenant_created_id")
    op.drop_table("device_read_model")
