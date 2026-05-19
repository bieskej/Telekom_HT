"""msisdn.karantena_razlog za dvosmjernu karantenu

Revision ID: 005_karantena_razlog
Revises: 004_email_log
Create Date: 2026-05-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005_karantena_razlog"
down_revision: Union[str, None] = "004_email_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("msisdn", sa.Column("karantena_razlog", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("msisdn", "karantena_razlog")
