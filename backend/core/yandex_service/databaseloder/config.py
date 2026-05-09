from __future__ import annotations

from pathlib import Path

from core.yandex_service.databaseloder.dto import DbLoaderSettingsDTO
from services.settings import settings


def _parse_bool(raw_value: str | None, default: bool) -> bool:
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_path(value: str) -> Path:
    path = Path(value.strip())
    if path.is_absolute():
        return path
    return (Path.cwd() / path).resolve()


def load_loader_settings_from_env() -> DbLoaderSettingsDTO:
    dataset_dir_raw = settings.YANDEX_MVP_DATASET_DIR
    if not dataset_dir_raw:
        raise ValueError(
            "YANDEX_MVP_DATASET_DIR is not configured. "
            "Set an absolute or project-relative path to MVP dataset."
        )

    dataset_dir = _resolve_path(str(dataset_dir_raw))
    report_path_raw = settings.YANDEX_DB_LOADER_REPORT_PATH
    report_path = (
        _resolve_path(str(report_path_raw))
        if report_path_raw
        else (dataset_dir / "db_load_report.json").resolve()
    )

    return DbLoaderSettingsDTO(
        dataset_dir=dataset_dir,
        enabled=_parse_bool(str(settings.YANDEX_DB_LOADER_ENABLED), default=False),
        fail_on_error=_parse_bool(str(settings.YANDEX_DB_LOADER_FAIL_ON_ERROR), default=True),
        dry_run=_parse_bool(str(settings.YANDEX_DB_LOADER_DRY_RUN), default=False),
        report_path=report_path,
    )


def validate_dataset_directory(dataset_dir: Path) -> None:
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory does not exist: {dataset_dir}")
    if not dataset_dir.is_dir():
        raise NotADirectoryError(f"Dataset path is not a directory: {dataset_dir}")

    dataset_index_path = dataset_dir / "dataset_index.json"
    cards_dir = dataset_dir / "cards_info"

    if not dataset_index_path.exists():
        raise FileNotFoundError(f"dataset_index.json is missing: {dataset_index_path}")
    if not cards_dir.exists() or not cards_dir.is_dir():
        raise FileNotFoundError(f"cards_info directory is missing: {cards_dir}")
