import uuid
from enum import Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class UserRole(Enum):
    """Роли пользователей в системе."""
    GUEST = "GUEST"
    MAINTAINER = "MAINTAINER"
    VIEWER = "VIEWER"


class StreamingService(Enum):
    """Доступные стриминговые сервисы."""
    SPOTIFY = "SPOTIFY"
    YOUTUBE = "YOUTUBE"
    YANDEX_MUSIC = "YANDEX_MUSIC"


class Base(DeclarativeBase):
    """Базовый класс для декларативных моделей SQLAlchemy."""
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )