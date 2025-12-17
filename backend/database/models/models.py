import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from backend.database.models.base import UserRole, StreamingService

# === Base и Enums ===

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для декларативных моделей SQLAlchemy."""
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )


# === ДОМЕННАЯ ОБЛАСТЬ ===

class User(Base):
    """
    Сущность Пользователь.

    Связи:
    - `credentials`: Один ко многим с UserCredential (1:*), для хранения токенов.
    - `connections`: Один ко многим с Connection (1:*), для участия в группах.
    - `tracks_added`: Один ко многим с Track (1:*), треки, добавленные пользователем.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Связи (Relationship)
    credentials: Mapped[List["UserCredential"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    connections: Mapped[List["Connection"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    tracks_added: Mapped[List["Track"]] = relationship(
        back_populates="added_by_user"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, name='{self.name}', role='{self.role.name}')"


class Group(Base):
    """
    Сущность Группа/Комната для совместного прослушивания.

    Связи:
    - `playlist`: Один к одному с Playlist (1:1), плейлист группы.
    - `connections`: Один ко многим с Connection (1:*), участники группы.
    """
    __tablename__ = "groups"

    name: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)

    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    connections: Mapped[List["Connection"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Group(id={self.id}, code='{self.code}', is_active={self.is_public})"


class GroupQr(Base):
    __tablename__ = "groupqr"
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id"), unique=True, nullable=False
    )
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    expired_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )


class Connection(Base):
    """
    Сущность Связь (соединительная таблица) между User и Group.
    Отражает участие пользователя в группе и его роль в этой группе.

    Связи:
    - `user`: Многие к одному с User (*:1).
    - `group`: Многие к одному с Group (*:1).
    """
    __tablename__ = "connections"

    # Составной первичный ключ (User_ID + Group_ID)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), primary_key=True
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id"), primary_key=True
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="connection_role_enum"),
        default=UserRole.VIEWER,
        nullable=False,
    )

    # Связи (Relationship)
    user: Mapped["User"] = relationship(back_populates="connections")
    group: Mapped["Group"] = relationship(back_populates="connections")

    def __repr__(self) -> str:
        return (
            f"Connection(user_id={self.user_id}, group_id={self.group_id}, "
            f"role='{self.role.name}')"
        )


class Playlist(Base):
    """
    Сущность Плейлист.
    Тесно связан с Group (1:1).

    Связи:
    - `group`: Один к одному с Group (1:1).
    - `tracks`: Один ко многим с Track (1:*), треки в плейлисте.
    """
    __tablename__ = "playlists"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )

    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id"), primary_key=True
    )

    # Внешний ключ для 1:1 связи с Group.
    current_track_index: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    tracks: Mapped[List["Track"]] = relationship(
        back_populates="playlist", order_by="Track.added_at", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"Playlist(id={self.id}, group_id={self.group_id}, "
            f"current_track_index={self.current_track_index})"
        )


class Track(Base):
    """
    Сущность Трек.

    Связи:
    - `playlist`: Многие к одному с Playlist (*:1).
    - `added_by_user`: Многие к одному с User (*:1), пользователь, добавивший трек.
    - `service`: Многие к одному с StreamingService (*:1).
    """
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # Добавим простой int ID для удобства

    playlist_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("playlists.id"), nullable=False
    )
    added_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    service: Mapped[StreamingService] = mapped_column(
        Enum(StreamingService, name="streaming_service_enum"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    duration: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # Продолжительность в секундах
    external_url: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Ссылка/ID трека на внешнем сервисе
    added_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )

    # Связи (Relationship)
    playlist: Mapped["Playlist"] = relationship(back_populates="tracks")
    added_by_user: Mapped["User"] = relationship(back_populates="tracks_added")

    def __repr__(self) -> str:
        return (
            f"Track(id={self.id}, title='{self.title[:30]}...', "
            f"service='{self.service.name}', playlist_id={self.playlist_id})"
        )


class UserCredential(Base):
    """
    Сущность Учетные данные пользователя для внешних сервисов.

    Связи:
    - `user`: Многие к одному с User (*:1).
    - `service`: Многие к одному с StreamingService (*:1).
    """
    __tablename__ = "user_credentials"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    service: Mapped[StreamingService] = mapped_column(
        Enum(StreamingService, name="cred_service_enum"),
        nullable=False,
    )

    token: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Предполагаем, что токен может быть длинным
    expiry: Mapped[datetime] = mapped_column(
        DateTime, nullable=True
    )

    # Связи (Relationship)
    user: Mapped["User"] = relationship(back_populates="credentials")

    def __repr__(self) -> str:
        return (
            f"UserCredential(id={self.id}, user_id={self.user_id}, "
            f"service='{self.service.name}', expiry={self.expiry})"
        )


# --- Пример настройки (для демонстрации) ---
from sqlalchemy import create_engine
# engine = create_engine("sqlite:///./example.db")
# Base.metadata.create_all(engine)
