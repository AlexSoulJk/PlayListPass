"""drop legacy tracks.playlist_id and keep playlist_tracks M:N

Revision ID: 4a7f6d1c2b99
Revises: 6a9c9c5b13a8
Create Date: 2026-05-10 02:00:00.000000

"""

from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4a7f6d1c2b99"
down_revision: Union[str, Sequence[str], None] = "6a9c9c5b13a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    legacy_rows = bind.execute(
        sa.text("SELECT id, playlist_id FROM tracks WHERE playlist_id IS NOT NULL")
    ).fetchall()

    for row in legacy_rows:
        bind.execute(
            sa.text(
                """
                INSERT INTO playlist_tracks (id, playlist_id, track_id, position, added_at)
                VALUES (:id, :playlist_id, :track_id, NULL, NOW())
                ON CONFLICT (playlist_id, track_id) DO NOTHING
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "playlist_id": row.playlist_id,
                "track_id": row.id,
            },
        )

    op.drop_column("tracks", "playlist_id")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("tracks", sa.Column("playlist_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "tracks_playlist_id_fkey",
        "tracks",
        "playlists",
        ["playlist_id"],
        ["id"],
    )

    # Restore a single "primary" playlist relation per track as first added link.
    op.execute(
        sa.text(
            """
            UPDATE tracks AS t
            SET playlist_id = src.playlist_id
            FROM (
                SELECT DISTINCT ON (track_id) track_id, playlist_id
                FROM playlist_tracks
                ORDER BY track_id, added_at ASC, id ASC
            ) AS src
            WHERE src.track_id = t.id
            """
        )
    )
