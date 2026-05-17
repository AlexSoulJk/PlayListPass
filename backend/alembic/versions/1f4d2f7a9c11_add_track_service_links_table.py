"""add track service links table for cross-service track identity

Revision ID: 1f4d2f7a9c11
Revises: 4a7f6d1c2b99
Create Date: 2026-05-17 17:30:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "1f4d2f7a9c11"
down_revision: Union[str, Sequence[str], None] = "4a7f6d1c2b99"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _service_enum() -> sa.Enum:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql.ENUM(
            "SPOTIFY",
            "YOUTUBE",
            "YANDEX_MUSIC",
            name="streaming_service_enum",
            create_type=False,
        )
    return sa.Enum(
        "SPOTIFY",
        "YOUTUBE",
        "YANDEX_MUSIC",
        name="streaming_service_enum",
        native_enum=False,
    )


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "track_service_links",
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("service", _service_enum(), nullable=False),
        sa.Column("service_track_id", sa.String(length=191), nullable=False),
        sa.Column("external_url", sa.Text(), nullable=True),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
        sa.Column(
            "imported_from_search",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("fetched_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service", "service_track_id", name="uq_track_service_link"),
    )
    op.create_index(
        "ix_track_service_links_track_id",
        "track_service_links",
        ["track_id"],
        unique=False,
    )
    op.create_index(
        "ix_track_service_links_service_track_id",
        "track_service_links",
        ["service", "service_track_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_track_service_links_service_track_id",
        table_name="track_service_links",
    )
    op.drop_index(
        "ix_track_service_links_track_id",
        table_name="track_service_links",
    )
    op.drop_table("track_service_links")
