from __future__ import annotations

import json
import traceback
from datetime import datetime
from pathlib import Path

from core.yandex_service.databaseloder.dto import LoadErrorDTO, LoadStatsDTO


def create_stats(*, total_cards: int) -> LoadStatsDTO:
    return LoadStatsDTO(started_at=datetime.utcnow(), total_cards=total_cards)


def finalize_stats(stats: LoadStatsDTO) -> LoadStatsDTO:
    stats.finished_at = datetime.utcnow()
    stats.errors_count = len(stats.errors)
    return stats


def append_error(
    *,
    stats: LoadStatsDTO,
    service_track_id: str | None,
    stage: str,
    error_type: str,
    message: str,
    with_traceback: bool = False,
) -> None:
    tb_text = traceback.format_exc() if with_traceback else None
    stats.errors.append(
        LoadErrorDTO(
            service_track_id=service_track_id,
            stage=stage,
            error_type=error_type,
            message=message,
            traceback=tb_text,
        )
    )


def write_report(*, stats: LoadStatsDTO, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = stats.model_dump(mode="json")
    report_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
