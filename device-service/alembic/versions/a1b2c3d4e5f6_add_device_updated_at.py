"""add_device_updated_at

Revision ID: a1b2c3d4e5f6
Revises: 83e79a6b2458
Create Date: 2026-02-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '83e79a6b2458'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Default updated_at to created_at for existing rows via a two-step approach:
    # 1. Add the column as nullable with no default
    # 2. Backfill from created_at
    # 3. Set NOT NULL
    op.add_column("devices", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE devices SET updated_at = created_at WHERE updated_at IS NULL")
    op.alter_column("devices", "updated_at", nullable=False)


def downgrade() -> None:
    op.drop_column("devices", "updated_at")
