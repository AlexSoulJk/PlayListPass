"""make tracks.playlist_id nullable after applied prior revision

Revision ID: 6a9c9c5b13a8
Revises: 2d6d81b7f701
Create Date: 2026-05-10 00:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6a9c9c5b13a8"
down_revision: Union[str, Sequence[str], None] = "2d6d81b7f701"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "tracks",
        "playlist_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "tracks",
        "playlist_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
