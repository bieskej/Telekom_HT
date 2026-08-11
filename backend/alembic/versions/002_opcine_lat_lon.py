"""dodaj lat i lon kolone na opcine za mapu choropleth

Revision ID: 002_opcine_lat_lon
Revises: 001_adresa_placanja
Create Date: 2026-05-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_opcine_lat_lon"
down_revision: Union[str, None] = "001_adresa_placanja"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("opcine", sa.Column("lat", sa.Float(), nullable=True))
    op.add_column("opcine", sa.Column("lon", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("opcine", "lon")
    op.drop_column("opcine", "lat")
