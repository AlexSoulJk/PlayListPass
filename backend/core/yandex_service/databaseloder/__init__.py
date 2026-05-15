from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.yandex_service.databaseloder.service import YandexDatasetLoaderService

__all__ = ["YandexDatasetLoaderService"]


def __getattr__(name: str):
    if name == "YandexDatasetLoaderService":
        from core.yandex_service.databaseloder.service import YandexDatasetLoaderService

        return YandexDatasetLoaderService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
