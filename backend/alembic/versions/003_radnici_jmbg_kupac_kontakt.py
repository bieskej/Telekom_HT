"""radnici.jmbg + tablica kupac_kontakt za portal kupaca

Revision ID: 003_radnici_jmbg_kupac
Revises: 002_opcine_lat_lon
Create Date: 2026-05-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_radnici_jmbg_kupac"
down_revision: Union[str, None] = "002_opcine_lat_lon"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("radnici", sa.Column("jmbg", sa.String(length=13), nullable=True))
    op.execute("ALTER TABLE radnici DROP CONSTRAINT IF EXISTS radnici_uloga_check")
    op.execute(
        "ALTER TABLE radnici ADD CONSTRAINT radnici_uloga_check "
        "CHECK (uloga IN ('admin', 'prodaja', 'promet', 'kupac'))"
    )
    op.create_table(
        "kupac_kontakt",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("kupac_id", sa.Integer(), sa.ForeignKey("radnici.id"), nullable=False),
        sa.Column("predmet", sa.String(length=255), nullable=False),
        sa.Column("poruka", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("kupac_kontakt")
    op.execute("ALTER TABLE radnici DROP CONSTRAINT IF EXISTS radnici_uloga_check")
    op.execute(
        "ALTER TABLE radnici ADD CONSTRAINT radnici_uloga_check "
        "CHECK (uloga IN ('admin', 'prodaja', 'promet'))"
    )
    op.drop_column("radnici", "jmbg")
