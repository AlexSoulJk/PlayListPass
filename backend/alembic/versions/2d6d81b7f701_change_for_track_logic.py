"""Change for track logic

Revision ID: 2d6d81b7f701
Revises: b91ab4f8c3d2
Create Date: 2026-05-09 23:30:08.633254

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d6d81b7f701'
down_revision: Union[str, Sequence[str], None] = 'b91ab4f8c3d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Align with DTO/loader requirements:
    # - catalog tracks may exist without concrete playlist/user ownership
    # - legacy url columns are dropped in favor of storage keys
    op.alter_column(
        "tracks",
        "playlist_id",
        existing_type=sa.UUID(),
        nullable=True,
    )
    op.alter_column('tracks', 'added_by_user_id',
               existing_type=sa.UUID(),
               nullable=True)
    op.drop_column('tracks', 'audio_url')
    op.drop_column('tracks', 'image_url')


def downgrade() -> None:
    """Downgrade schema."""
    # Restore legacy columns first as nullable to allow backfill.
    op.add_column(
        "tracks",
        sa.Column("image_url", sa.VARCHAR(length=1000), autoincrement=False, nullable=True),
    )
    op.add_column(
        "tracks",
        sa.Column("audio_url", sa.VARCHAR(length=1000), autoincrement=False, nullable=True),
    )

    # Best-effort backfill from policy-safe storage fields.
    op.execute(
        sa.text(
            "UPDATE tracks SET image_url = cover_storage_key "
            "WHERE image_url IS NULL AND cover_storage_key IS NOT NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE tracks SET audio_url = audio_storage_key "
            "WHERE audio_url IS NULL AND audio_storage_key IS NOT NULL"
        )
    )
    op.execute(sa.text("UPDATE tracks SET audio_url = '' WHERE audio_url IS NULL"))

    op.alter_column(
        "tracks",
        "audio_url",
        existing_type=sa.VARCHAR(length=1000),
        nullable=False,
    )
    op.alter_column('tracks', 'added_by_user_id',
               existing_type=sa.UUID(),
               nullable=False)
    op.alter_column(
        "tracks",
        "playlist_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
