from __future__ import annotations

import json
from pathlib import Path, PureWindowsPath

from core.yandex_service.databaseloder.dto import DatasetIndexItemDTO, TrackCardDTO


def read_dataset_index(dataset_dir: Path) -> list[DatasetIndexItemDTO]:
    dataset_index_path = dataset_dir / "dataset_index.json"
    raw_payload = json.loads(dataset_index_path.read_text(encoding="utf-8"))
    return [DatasetIndexItemDTO.model_validate(item) for item in raw_payload]


def resolve_card_file_path(dataset_dir: Path, card_path: str) -> Path:
    candidate = Path(card_path)
    if not candidate.is_absolute():
        candidate = dataset_dir / candidate
    return candidate.resolve()


def read_track_card(dataset_dir: Path, index_item: DatasetIndexItemDTO) -> TrackCardDTO:
    card_file_path = resolve_card_file_path(dataset_dir=dataset_dir, card_path=index_item.card_path)
    if not card_file_path.exists():
        raise FileNotFoundError(
            f"Card file was not found for track {index_item.service_track_id}: {card_file_path}"
        )
    raw_payload = json.loads(card_file_path.read_text(encoding="utf-8"))
    return TrackCardDTO.model_validate(raw_payload)


def resolve_local_artifact_path(
    *,
    dataset_dir: Path,
    raw_path: str | None,
    fallback_subdir: str,
) -> Path | None:
    if not raw_path:
        return None

    source_path = Path(raw_path)
    if source_path.exists():
        return source_path.resolve()

    filename = source_path.name
    # Handle Windows absolute paths when loader runs on Linux container.
    if ("\\" in raw_path or ":" in raw_path) and not filename:
        filename = PureWindowsPath(raw_path).name
    elif "\\" in raw_path or ":" in raw_path:
        win_name = PureWindowsPath(raw_path).name
        if win_name:
            filename = win_name

    fallback_path = (dataset_dir / fallback_subdir / filename).resolve()
    if fallback_path.exists():
        return fallback_path

    return None
