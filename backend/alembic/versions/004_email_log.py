"""tablica email_log za audit HTML emailova

Revision ID: 004_email_log
Revises: 003_radnici_jmbg_kupac
Create Date: 2026-05-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_email_log"
down_revision: Union[str, None] = "003_radnici_jmbg_kupac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("msisdn_id", sa.Integer(), sa.ForeignKey("msisdn.id"), nullable=True),
        sa.Column("primatelj", sa.String(length=255), nullable=False),
        sa.Column("predmet", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("html_tijelo", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("email_log")
