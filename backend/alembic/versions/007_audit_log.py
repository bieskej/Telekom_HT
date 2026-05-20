"""audit_log tablica

Revision ID: 007_audit_log
Revises: 006_portabilnost_servisni
Create Date: 2026-05-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007_audit_log"
down_revision: Union[str, None] = "006_portabilnost_servisni"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("radnik_id", sa.Integer(), sa.ForeignKey("radnici.id"), nullable=True),
        sa.Column("akcija", sa.String(length=80), nullable=False),
        sa.Column("entitet", sa.String(length=50), nullable=False),
        sa.Column("entitet_id", sa.Integer(), nullable=True),
        sa.Column("detalji_json", sa.Text(), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
