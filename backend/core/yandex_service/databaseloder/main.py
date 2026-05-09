from __future__ import annotations

import asyncio
from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from core.yandex_service.databaseloder.config import (
    load_loader_settings_from_env,
    validate_dataset_directory,
)
from core.yandex_service.databaseloder.service import YandexDatasetLoaderService
from database.session import async_session_maker
from services.storage.factory import get_s3_storage_service


async def run_loader(*, cleanup_only: bool = False) -> int:
    settings = load_loader_settings_from_env()
    validate_dataset_directory(settings.dataset_dir)

    if not settings.enabled and not cleanup_only:
        print("Yandex DB loader is disabled (YANDEX_DB_LOADER_ENABLED=false).")
        return 0

    service = YandexDatasetLoaderService(
        session_maker=async_session_maker,
        storage_service=get_s3_storage_service(),
    )

    if cleanup_only:
        cleanup = await service.clear_uploaded_files(settings)
        print(
            "Yandex DB loader cleanup completed. "
            f"attempted={cleanup.attempted}, "
            f"deleted={cleanup.deleted}, "
            f"missing={cleanup.missing}, "
            f"errors={cleanup.errors}"
        )
        return 1 if cleanup.errors > 0 else 0

    stats = await service.run(settings)

    print(
        "Yandex DB loader completed. "
        f"imported={stats.imported_tracks}, "
        f"updated={stats.updated_tracks}, "
        f"skipped={stats.skipped_invalid}, "
        f"errors={stats.errors_count}, "
        f"report={settings.report_path}"
    )
    if settings.fail_on_error and stats.errors_count > 0:
        return 1
    return 0


def main() -> None:
    cleanup_only = "--cleanup" in sys.argv
    exit_code = asyncio.run(run_loader(cleanup_only=cleanup_only))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
