"""portabilnost, servisni_nalog, msisdn.u_kvaru

Revision ID: 006_portabilnost_servisni
Revises: 005_karantena_razlog
Create Date: 2026-05-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006_portabilnost_servisni"
down_revision: Union[str, None] = "005_karantena_razlog"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE msisdn DROP CONSTRAINT IF EXISTS msisdn_status_check")
    op.execute(
        """
        ALTER TABLE msisdn ADD CONSTRAINT msisdn_status_check
        CHECK (status IN ('slobodan', 'zauzet', 'karantena', 'portano'))
        """
    )
    op.add_column(
        "msisdn",
        sa.Column("u_kvaru", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "portabilnost",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("msisdn_id", sa.Integer(), sa.ForeignKey("msisdn.id"), nullable=True),
        sa.Column("broj", sa.String(length=15), nullable=True),
        sa.Column("tip", sa.String(length=20), nullable=False),
        sa.Column("izvor_op", sa.String(length=100), nullable=False),
        sa.Column("ciljni_op", sa.String(length=100), nullable=False),
        sa.Column("datum_zahtjeva", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("datum_realizacije", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="zahtjev"),
        sa.Column("napomena", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("radnici.id"), nullable=True),
    )
    op.create_table(
        "servisni_nalog",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uredjaj_id", sa.Integer(), sa.ForeignKey("uredjaji.id"), nullable=False),
        sa.Column("opis", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="otvoren"),
        sa.Column("prioritet", sa.String(length=20), nullable=False, server_default="srednji"),
        sa.Column("prijavio_id", sa.Integer(), sa.ForeignKey("radnici.id"), nullable=True),
        sa.Column("rijesio_id", sa.Integer(), sa.ForeignKey("radnici.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("rijeseno_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("servisni_nalog")
    op.drop_table("portabilnost")
    op.drop_column("msisdn", "u_kvaru")
