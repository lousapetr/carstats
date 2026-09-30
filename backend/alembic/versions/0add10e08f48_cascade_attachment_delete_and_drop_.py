"""cascade attachment delete and drop orphans

Revision ID: 0add10e08f48
Revises: c1ee3d6690cd
Create Date: 2026-09-30 12:15:01.251730

"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.config import settings


# revision identifiers, used by Alembic.
revision: str = '0add10e08f48'
down_revision: Union[str, Sequence[str], None] = 'c1ee3d6690cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The original FK was created unnamed; a naming convention lets batch mode
# find it to drop it.
NAMING_CONVENTION = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}
FK_NAME = "fk_attachment_service_entry_id_serviceentry"

# An attachment is orphaned if its entry is gone, or if its entry id was
# reused by a newer entry: attachments are always uploaded after their
# entry exists, so one older than its "parent" belonged to a deleted one.
ORPHANS = """
    SELECT a.id, a.path FROM attachment a
    LEFT JOIN serviceentry s ON s.id = a.service_entry_id
    WHERE s.id IS NULL OR a.uploaded_at < s.created_at
"""


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    orphans = conn.execute(sa.text(ORPHANS)).all()
    for attachment_id, path in orphans:
        conn.execute(sa.text("DELETE FROM attachment WHERE id = :id"), {"id": attachment_id})
        (Path(settings.uploads_dir) / path).unlink(missing_ok=True)

    with op.batch_alter_table(
        "attachment", recreate="always", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        batch_op.drop_constraint(FK_NAME, type_="foreignkey")
        batch_op.create_foreign_key(
            FK_NAME, "serviceentry", ["service_entry_id"], ["id"], ondelete="CASCADE"
        )


def downgrade() -> None:
    """Downgrade schema. The deleted orphans are not restored."""
    with op.batch_alter_table("attachment", recreate="always") as batch_op:
        batch_op.drop_constraint(FK_NAME, type_="foreignkey")
        batch_op.create_foreign_key(FK_NAME, "serviceentry", ["service_entry_id"], ["id"])
