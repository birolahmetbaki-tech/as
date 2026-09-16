"""uretim kaydinda tarih ve birim benzersiz

Revision ID: 26b1da15eda9
Revises: 941e3e6b5659
Create Date: 2026-09-16
"""

from collections.abc import Sequence

from alembic import op

revision: str = "26b1da15eda9"
down_revision: str | None = "941e3e6b5659"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("production") as batch_op:
        batch_op.create_unique_constraint(
            "uq_production_date_unit", ["production_date", "unit"]
        )


def downgrade() -> None:
    with op.batch_alter_table("production") as batch_op:
        batch_op.drop_constraint("uq_production_date_unit", type_="unique")
