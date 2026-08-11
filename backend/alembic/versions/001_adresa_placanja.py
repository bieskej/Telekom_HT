"""adresa na msisdn i tablica placanja

Revision ID: 001_adresa_placanja
Revises:
Create Date: 2026-05-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_adresa_placanja"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("msisdn", sa.Column("adresa", sa.Text(), nullable=True))
    op.add_column("msisdn", sa.Column("grad", sa.String(length=100), nullable=True))
    op.add_column("msisdn", sa.Column("postanski_broj", sa.String(length=10), nullable=True))

    op.create_table(
        "placanja",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("msisdn_id", sa.Integer(), sa.ForeignKey("msisdn.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nacin", sa.String(length=20), nullable=False),
        sa.Column("broj_kartice_hash", sa.String(length=128), nullable=True),
        sa.Column("datum_isteka", sa.String(length=7), nullable=True),
        sa.Column("cvv_hash", sa.String(length=128), nullable=True),
        sa.Column("ime_vlasnika", sa.String(length=255), nullable=True),
        sa.Column("iznos", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="izvrseno", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_placanja_msisdn_id", "placanja", ["msisdn_id"])


def downgrade() -> None:
    op.drop_index("idx_placanja_msisdn_id", table_name="placanja")
    op.drop_table("placanja")
    op.drop_column("msisdn", "postanski_broj")
    op.drop_column("msisdn", "grad")
    op.drop_column("msisdn", "adresa")
