"""add track provider and artist normalized tables

Revision ID: b91ab4f8c3d2
Revises: 4e3a5e0acfb3
Create Date: 2026-05-09 22:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b91ab4f8c3d2"
down_revision: Union[str, Sequence[str], None] = "4e3a5e0acfb3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    existing_streaming_service_enum = postgresql.ENUM(
        "SPOTIFY",
        "YOUTUBE",
        "YANDEX_MUSIC",
        name="streaming_service_enum",
        create_type=False,
    )

    op.add_column("tracks", sa.Column("duration_ms", sa.Integer(), nullable=True))
    op.add_column("tracks", sa.Column("cover_storage_key", sa.String(length=1000), nullable=True))
    op.add_column("tracks", sa.Column("audio_storage_key", sa.String(length=1000), nullable=True))
    op.add_column(
        "tracks",
        sa.Column("audio_valid_for_mvp", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("tracks", sa.Column("release_date", sa.DateTime(), nullable=True))
    op.add_column("tracks", sa.Column("fetched_at", sa.DateTime(), nullable=True))
    op.create_index("ix_tracks_title", "tracks", ["title"], unique=False)

    op.create_table(
        "artists",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_artists_name", "artists", ["name"], unique=False)

    op.create_table(
        "artist_service_links",
        sa.Column("artist_id", sa.Uuid(), nullable=False),
        sa.Column(
            "service",
            existing_streaming_service_enum,
            nullable=False,
        ),
        sa.Column("service_artist_id", sa.String(length=128), nullable=False),
        sa.Column("service_artist_name", sa.String(length=255), nullable=True),
        sa.Column("external_url", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service", "service_artist_id", name="uq_artist_service_id"),
    )
    op.create_index(
        "ix_artist_service_links_artist_id",
        "artist_service_links",
        ["artist_id"],
        unique=False,
    )

    op.create_table(
        "playlist_tracks",
        sa.Column("playlist_id", sa.Uuid(), nullable=False),
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["playlist_id"], ["playlists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("playlist_id", "track_id", name="uq_playlist_track"),
    )
    op.create_index(
        "ix_playlist_tracks_playlist_id",
        "playlist_tracks",
        ["playlist_id"],
        unique=False,
    )
    op.create_index(
        "ix_playlist_tracks_track_id",
        "playlist_tracks",
        ["track_id"],
        unique=False,
    )

    op.create_table(
        "track_artists",
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("artist_id", sa.Uuid(), nullable=False),
        sa.Column("artist_order", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(length=64), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("track_id", "artist_id", name="uq_track_artist"),
    )
    op.create_index("ix_track_artists_track_id", "track_artists", ["track_id"], unique=False)
    op.create_index("ix_track_artists_artist_id", "track_artists", ["artist_id"], unique=False)

    op.create_table(
        "yandex_tracks",
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("yandex_track_id", sa.String(length=128), nullable=False),
        sa.Column("yandex_album_id", sa.String(length=128), nullable=True),
        sa.Column("play_count", sa.BigInteger(), nullable=True),
        sa.Column("likes_count", sa.BigInteger(), nullable=True),
        sa.Column("lyrics_available", sa.Boolean(), nullable=True),
        sa.Column("lyrics_available_set", sa.Boolean(), nullable=True),
        sa.Column("codec", sa.String(length=32), nullable=True),
        sa.Column("bitrate_kbps", sa.Integer(), nullable=True),
        sa.Column("provider_fetched_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("track_id"),
        sa.UniqueConstraint("yandex_track_id"),
    )
    op.create_index(
        "ix_yandex_tracks_yandex_track_id",
        "yandex_tracks",
        ["yandex_track_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_yandex_tracks_yandex_track_id", table_name="yandex_tracks")
    op.drop_table("yandex_tracks")

    op.drop_index("ix_track_artists_artist_id", table_name="track_artists")
    op.drop_index("ix_track_artists_track_id", table_name="track_artists")
    op.drop_table("track_artists")

    op.drop_index("ix_playlist_tracks_track_id", table_name="playlist_tracks")
    op.drop_index("ix_playlist_tracks_playlist_id", table_name="playlist_tracks")
    op.drop_table("playlist_tracks")

    op.drop_index("ix_artist_service_links_artist_id", table_name="artist_service_links")
    op.drop_table("artist_service_links")

    op.drop_index("ix_artists_name", table_name="artists")
    op.drop_table("artists")

    op.drop_index("ix_tracks_title", table_name="tracks")
    op.drop_column("tracks", "fetched_at")
    op.drop_column("tracks", "release_date")
    op.drop_column("tracks", "audio_valid_for_mvp")
    op.drop_column("tracks", "audio_storage_key")
    op.drop_column("tracks", "cover_storage_key")
    op.drop_column("tracks", "duration_ms")
