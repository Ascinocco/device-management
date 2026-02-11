"""outbox_attempts

Revision ID: 83e79a6b2458
Revises: 89948eec703a
Create Date: 2026-02-07 23:00:09.749969

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83e79a6b2458'
down_revision: Union[str, Sequence[str], None] = '89948eec703a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("outbox", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("outbox", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("outbox", sa.Column("last_error", sa.String(length=512), nullable=True))
    op.alter_column("outbox", "attempts", server_default=None)


def downgrade() -> None:
    op.drop_column("outbox", "last_error")
    op.drop_column("outbox", "attempts")
    op.drop_column("outbox", "processed_at")
