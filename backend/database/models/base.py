from enum import Enum




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