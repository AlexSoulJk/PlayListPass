from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Данные БД (читаются из переменных окружения Docker)
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DATABASE_URL: str

    # Секретный ключ для JWT (нужно добавить в docker-compose или .env файл docker'а)
    SECRET_KEY: str = "UNSAFE_DEFAULT_SECRET_CHANGE_ME"

    model_config = SettingsConfigDict(extra="ignore")


# Основной файл из Docker
docker_env = Path(__file__).parent.parent.parent / "docker" / ".env"
# Локальный файл переопределений (можно положить в корень проекта)
override_env = Path(__file__).parent.parent.parent / ".env.override"

# Если есть override, загружаем его тоже (он имеет приоритет)
if override_env.exists():
    settings = Settings(_env_file=[docker_env, override_env])
    print(settings.model_dump())
else:
    settings = Settings(_env_file=docker_env)
