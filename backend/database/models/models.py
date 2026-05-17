import uuid
from datetime import datetime
from typing import List, Optional

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, StreamingService, UserRole


class User(SQLAlchemyBaseUserTableUUID, Base):
    """
    User c полями от FastAPI Users (email, password, etc) + твои поля.
    """
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Связи
    credentials: Mapped[List["UserCredential"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    connections: Mapped[List["Connection"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    tracks_added: Mapped[List["Track"]] = relationship(back_populates="added_by_user")

    def __repr__(self) -> str:
        return f"User(id={self.id}, email='{self.email}', name='{self.name}')"


class Group(Base):
    """
    Сущность Группа/Комната для совместного прослушивания.

    Связи:
    - `connections`: Один ко многим с Connection (1:*), участники группы.
    """
    __tablename__ = "groups"

    name: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    connections: Mapped[List["Connection"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    playlists: Mapped[List["Playlist"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"Group(id={self.id}, name={self.name}, is_public={self.is_public}, "
            f"image_url='{self.image_url}')"
        )


class GroupQr(Base):
    __tablename__ = "groupqr"

    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id"), unique=True, nullable=False
    )
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    expired_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


class Connection(Base):
    __tablename__ = "connections"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("groups.id"))
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="connection_role_enum"),
        default=UserRole.VIEWER,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="connections")
    group: Mapped["Group"] = relationship(back_populates="connections")

    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_user_group"),
        Index("index_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return (
            f"Connection(user_id={self.user_id}, group_id={self.group_id}, "
            f"role='{self.role.name}')"
        )


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("groups.id"))
    current_track_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    group: Mapped["Group"] = relationship(back_populates="playlists")

    # New normalized relation for M:N playlists <-> tracks.
    playlist_tracks: Mapped[List["PlaylistTrack"]] = relationship(
        back_populates="playlist", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"Playlist(id={self.id}, group_id={self.group_id}, "
            f"current_track_index={self.current_track_index}, name='{self.name}', "
            f"image_url='{self.image_url}')"
        )



class Track(Base):
    """
    Сущность Трек.

    Связи:
    - `playlist`: Многие ко многим с Playlist (*:*).
    - `added_by_user`: Многие к одному с User (*:1), пользователь, добавивший трек.
    - `service`: Многие к одному с StreamingService (*:1).
    """
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    added_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    service: Mapped[StreamingService] = mapped_column(
        Enum(StreamingService, name="streaming_service_enum"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    external_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Policy-safe storage fields for new ingestion.
    cover_storage_key: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    audio_storage_key: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    audio_valid_for_mvp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    release_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    added_by_user: Mapped[Optional["User"]] = relationship(back_populates="tracks_added")

    # New normalized relations.
    playlist_tracks: Mapped[List["PlaylistTrack"]] = relationship(
        back_populates="track", cascade="all, delete-orphan"
    )
    yandex_meta: Mapped[Optional["YandexTrack"]] = relationship(
        back_populates="track",
        uselist=False,
        cascade="all, delete-orphan",
    )
    track_artists: Mapped[List["TrackArtist"]] = relationship(
        back_populates="track", cascade="all, delete-orphan"
    )
    service_links: Mapped[List["TrackServiceLink"]] = relationship(
        back_populates="track",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_tracks_title", "title"),)

    def __repr__(self) -> str:
        return f"Track(id={self.id}, title='{self.title[:30]}...', service='{self.service.name}')"


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    playlist_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
    )
    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    playlist: Mapped["Playlist"] = relationship(back_populates="playlist_tracks")
    track: Mapped["Track"] = relationship(back_populates="playlist_tracks")

    __table_args__ = (
        UniqueConstraint("playlist_id", "track_id", name="uq_playlist_track"),
        Index("ix_playlist_tracks_playlist_id", "playlist_id"),
        Index("ix_playlist_tracks_track_id", "track_id"),
    )


class TrackServiceLink(Base):
    __tablename__ = "track_service_links"

    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"),
        nullable=False,
    )
    service: Mapped[StreamingService] = mapped_column(
        Enum(StreamingService, name="streaming_service_enum"),
        nullable=False,
    )
    service_track_id: Mapped[str] = mapped_column(String(191), nullable=False)
    external_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    imported_from_search: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    track: Mapped["Track"] = relationship(back_populates="service_links")

    __table_args__ = (
        UniqueConstraint("service", "service_track_id", name="uq_track_service_link"),
        Index("ix_track_service_links_track_id", "track_id"),
        Index(
            "ix_track_service_links_service_track_id",
            "service",
            "service_track_id",
        ),
    )


class YandexTrack(Base):
    __tablename__ = "yandex_tracks"

    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    yandex_track_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    yandex_album_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    play_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    likes_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    lyrics_available: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    lyrics_available_set: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    codec: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    bitrate_kbps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    provider_fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    track: Mapped["Track"] = relationship(back_populates="yandex_meta")

    __table_args__ = (Index("ix_yandex_tracks_yandex_track_id", "yandex_track_id"),)


class Artist(Base):
    __tablename__ = "artists"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    service_links: Mapped[List["ArtistServiceLink"]] = relationship(
        back_populates="artist", cascade="all, delete-orphan"
    )
    track_artists: Mapped[List["TrackArtist"]] = relationship(
        back_populates="artist", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_artists_name", "name"),)

    def __repr__(self) -> str:
        return f"Artist(id={self.id}, name='{self.name}')"


class ArtistServiceLink(Base):
    __tablename__ = "artist_service_links"

    artist_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artists.id", ondelete="CASCADE"),
        nullable=False,
    )
    service: Mapped[StreamingService] = mapped_column(
        Enum(StreamingService, name="streaming_service_enum"),
        nullable=False,
    )
    service_artist_id: Mapped[str] = mapped_column(String(128), nullable=False)
    service_artist_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    external_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    artist: Mapped["Artist"] = relationship(back_populates="service_links")

    __table_args__ = (
        UniqueConstraint("service", "service_artist_id", name="uq_artist_service_id"),
        Index("ix_artist_service_links_artist_id", "artist_id"),
    )


class TrackArtist(Base):
    __tablename__ = "track_artists"

    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"),
        nullable=False,
    )
    artist_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artists.id", ondelete="CASCADE"),
        nullable=False,
    )
    artist_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    track: Mapped["Track"] = relationship(back_populates="track_artists")
    artist: Mapped["Artist"] = relationship(back_populates="track_artists")

    __table_args__ = (
        UniqueConstraint("track_id", "artist_id", name="uq_track_artist"),
        Index("ix_track_artists_track_id", "track_id"),
        Index("ix_track_artists_artist_id", "artist_id"),
    )


class UserCredential(Base):
    __tablename__ = "user_credentials"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    service: Mapped[StreamingService] = mapped_column(
        Enum(StreamingService, name="cred_service_enum"),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(Text, nullable=False)
    expiry: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="credentials")

    def __repr__(self) -> str:
        return (
            f"UserCredential(id={self.id}, user_id={self.user_id}, "
            f"service='{self.service.name}', expiry={self.expiry})"
        )
