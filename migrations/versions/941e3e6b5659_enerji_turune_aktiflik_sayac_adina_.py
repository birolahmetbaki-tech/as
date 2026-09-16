"""enerji turune aktiflik, sayac adina benzersizlik

Revision ID: 941e3e6b5659
Revises: 730452d9c554
Create Date: 2026-09-16 18:47:29.675963
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "941e3e6b5659"
down_revision: str | None = "730452d9c554"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Mevcut enerji turleri aktif kabul edilir.
    with op.batch_alter_table("energy_type") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
            )
        )

    with op.batch_alter_table("meter") as batch_op:
        batch_op.create_unique_constraint("uq_meter_name", ["name"])


def downgrade() -> None:
    with op.batch_alter_table("meter") as batch_op:
        batch_op.drop_constraint("uq_meter_name", type_="unique")

    with op.batch_alter_table("energy_type") as batch_op:
        batch_op.drop_column("is_active")
