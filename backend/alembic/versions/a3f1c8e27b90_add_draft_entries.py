"""add draft entries

Revision ID: a3f1c8e27b90
Revises: 0add10e08f48
Create Date: 2026-11-17 10:00:00.000000

"""

import shutil
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.config import settings


# revision identifiers, used by Alembic.
revision: str = "a3f1c8e27b90"
down_revision: Union[str, Sequence[str], None] = "0add10e08f48"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("fuelentry", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("is_draft", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.alter_column("date", existing_type=sa.DATE(), nullable=True)
        batch_op.alter_column("mileage_km", existing_type=sa.FLOAT(), nullable=True)
        batch_op.alter_column("liters", existing_type=sa.FLOAT(), nullable=True)
        batch_op.alter_column("price_per_liter", existing_type=sa.FLOAT(), nullable=True)

    with op.batch_alter_table("serviceentry", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("is_draft", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.alter_column("date", existing_type=sa.DATE(), nullable=True)
        batch_op.alter_column("mileage_km", existing_type=sa.FLOAT(), nullable=True)
        batch_op.alter_column("cost", existing_type=sa.FLOAT(), nullable=True)


def downgrade() -> None:
    """Downgrade schema; drafts cannot satisfy the NOT NULL columns, so they are deleted
    together with their attachments' files."""
    draft_service_ids = [
        row[0]
        for row in op.get_bind().execute(sa.text("SELECT id FROM serviceentry WHERE is_draft"))
    ]
    op.execute(
        "DELETE FROM attachment WHERE service_entry_id IN "
        "(SELECT id FROM serviceentry WHERE is_draft)"
    )
    op.execute("DELETE FROM serviceentry WHERE is_draft")
    op.execute("DELETE FROM fuelentry WHERE is_draft")

    with op.batch_alter_table("serviceentry", schema=None) as batch_op:
        batch_op.alter_column("cost", existing_type=sa.FLOAT(), nullable=False)
        batch_op.alter_column("mileage_km", existing_type=sa.FLOAT(), nullable=False)
        batch_op.alter_column("date", existing_type=sa.DATE(), nullable=False)
        batch_op.drop_column("is_draft")

    with op.batch_alter_table("fuelentry", schema=None) as batch_op:
        batch_op.alter_column("price_per_liter", existing_type=sa.FLOAT(), nullable=False)
        batch_op.alter_column("liters", existing_type=sa.FLOAT(), nullable=False)
        batch_op.alter_column("mileage_km", existing_type=sa.FLOAT(), nullable=False)
        batch_op.alter_column("date", existing_type=sa.DATE(), nullable=False)
        batch_op.drop_column("is_draft")

    # Files go last, once every schema change above has succeeded.
    for entry_id in draft_service_ids:
        shutil.rmtree(Path(settings.uploads_dir) / str(entry_id), ignore_errors=True)
