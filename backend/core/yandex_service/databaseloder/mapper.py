from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from database.models.base import StreamingService

from core.yandex_service.databaseloder.dto import (
    ArtistImportDTO,
    DatasetIndexItemDTO,
    TrackCardDTO,
    TrackImportBundleDTO,
    TrackUpsertDTO,
    YandexTrackUpsertDTO,
)


ALBUM_ID_PATTERN = re.compile(r"/album/(?P<album_id>\d+)")


def _to_naive_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _compute_duration_seconds(duration_ms: int | None) -> int:
    if not duration_ms or duration_ms < 0:
        return 0
    return int(duration_ms / 1000)


def _extract_album_id(external_url: str | None) -> str | None:
    if not external_url:
        return None
    match = ALBUM_ID_PATTERN.search(external_url)
    if not match:
        return None
    return match.group("album_id")


def _build_storage_key(
    *,
    source_path: Path | None,
    service_track_id: str,
    prefix: str,
) -> str | None:
    if source_path is None:
        return None
    extension = source_path.suffix.lower() or ".bin"
    return f"{prefix}/yandex/{service_track_id}{extension}"


def map_card_to_import_bundle(
    *,
    index_item: DatasetIndexItemDTO,
    card: TrackCardDTO,
    resolved_audio_path: Path | None,
    resolved_image_path: Path | None,
) -> TrackImportBundleDTO:
    external_url = card.external_url or card.external_url_row
    if not external_url:
        raise ValueError(
            f"Track {index_item.service_track_id} has no external_url/external_url_row in card payload."
        )

    track_payload = TrackUpsertDTO(
        service=StreamingService.YANDEX_MUSIC,
        title=card.title,
        duration_ms=card.duration_ms,
        duration=_compute_duration_seconds(card.duration_ms),
        external_url=external_url,
        audio_valid_for_mvp=bool(card.provider_info.valid_for_mvp),
        release_date=_to_naive_utc(card.release_date),
        fetched_at=_to_naive_utc(card.fetched_at),
        cover_storage_key=_build_storage_key(
            source_path=resolved_image_path,
            service_track_id=index_item.service_track_id,
            prefix="covers",
        ),
        audio_storage_key=_build_storage_key(
            source_path=resolved_audio_path,
            service_track_id=index_item.service_track_id,
            prefix="tracks",
        ),
        added_by_user_id=None,
    )

    yandex_payload = YandexTrackUpsertDTO(
        yandex_track_id=index_item.service_track_id,
        yandex_album_id=_extract_album_id(external_url),
        play_count=card.play_count,
        likes_count=card.likes_count,
        lyrics_available=card.lyrics_available,
        lyrics_available_set=card.lyrics_available_set,
        codec=card.provider_info.codec,
        bitrate_kbps=card.provider_info.bitrate_kbps,
        provider_fetched_at=_to_naive_utc(card.fetched_at),
    )

    artists = [
        ArtistImportDTO(
            service_artist_id=artist.service_artist_id,
            name=artist.name,
            order=position,
        )
        for position, artist in enumerate(card.artists)
    ]

    return TrackImportBundleDTO(
        service_track_id=index_item.service_track_id,
        track=track_payload,
        yandex_meta=yandex_payload,
        artists=artists,
    )
