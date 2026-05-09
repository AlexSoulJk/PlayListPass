from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from database.models.base import StreamingService


class DbLoaderSettingsDTO(BaseModel):
    dataset_dir: Path
    enabled: bool = False
    fail_on_error: bool = True
    dry_run: bool = False
    report_path: Path


class DatasetIndexItemDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    service_track_id: str = Field(min_length=1)
    card_path: str = Field(min_length=1)
    audio_path: str | None = None


class CardArtistDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    service_artist_id: str = Field(min_length=1)
    name: str = Field(min_length=1)


class CardProviderInfoDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    codec: str | None = None
    bitrate_kbps: int | None = None
    valid_for_mvp: bool = False


class CardLocalPathsDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    audio_path: str | None = None
    image_path: str | None = None
    lyrics_path: str | None = None


class TrackCardDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    service_track_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    artists: list[CardArtistDTO] = Field(default_factory=list)
    cover_url: str | None = None
    duration_ms: int | None = None
    external_url: str | None = None
    external_url_row: str | None = None
    release_date: datetime | None = None
    play_count: int | None = None
    likes_count: int | None = None
    lyrics_available: bool | None = None
    lyrics_available_set: bool | None = None
    provider_info: CardProviderInfoDTO = Field(default_factory=CardProviderInfoDTO)
    local_paths: CardLocalPathsDTO = Field(default_factory=CardLocalPathsDTO)
    fetched_at: datetime | None = None


class TrackUpsertDTO(BaseModel):
    service: StreamingService
    title: str
    duration_ms: int | None = None
    duration: int
    external_url: str
    audio_valid_for_mvp: bool
    release_date: datetime | None = None
    fetched_at: datetime | None = None
    cover_storage_key: str | None = None
    audio_storage_key: str | None = None
    added_by_user_id: uuid.UUID | None = None


class YandexTrackUpsertDTO(BaseModel):
    yandex_track_id: str
    yandex_album_id: str | None = None
    play_count: int | None = None
    likes_count: int | None = None
    lyrics_available: bool | None = None
    lyrics_available_set: bool | None = None
    codec: str | None = None
    bitrate_kbps: int | None = None
    provider_fetched_at: datetime | None = None


class ArtistUpsertDTO(BaseModel):
    name: str


class ArtistServiceLinkUpsertDTO(BaseModel):
    service: StreamingService
    service_artist_id: str
    service_artist_name: str | None = None
    external_url: str | None = None
    fetched_at: datetime | None = None
    artist_id: uuid.UUID | None = None


class TrackArtistLinkDTO(BaseModel):
    track_id: int
    artist_id: uuid.UUID
    artist_order: int | None = None
    role: str | None = None


class ArtistImportDTO(BaseModel):
    service_artist_id: str
    name: str
    order: int | None = None


class TrackImportBundleDTO(BaseModel):
    service_track_id: str
    track: TrackUpsertDTO
    yandex_meta: YandexTrackUpsertDTO
    artists: list[ArtistImportDTO] = Field(default_factory=list)


class LoadErrorDTO(BaseModel):
    service_track_id: str | None = None
    stage: str
    error_type: str
    message: str
    traceback: str | None = None


class LoadStatsDTO(BaseModel):
    started_at: datetime
    finished_at: datetime | None = None
    total_cards: int
    imported_tracks: int = 0
    updated_tracks: int = 0
    skipped_invalid: int = 0
    errors_count: int = 0
    errors: list[LoadErrorDTO] = Field(default_factory=list)
