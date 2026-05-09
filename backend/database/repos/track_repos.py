from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from core.yandex_service.databaseloder.dto import TrackUpsertDTO
from database.models.models import Track


class TrackRepos:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_track_by_id(self, track_id: int) -> Track | None:
        return await self.session.get(Track, track_id)

    async def create_track(self, payload: TrackUpsertDTO) -> Track:
        track = Track(
            added_by_user_id=payload.added_by_user_id,
            service=payload.service,
            title=payload.title,
            duration=payload.duration,
            duration_ms=payload.duration_ms,
            external_url=payload.external_url,
            cover_storage_key=payload.cover_storage_key,
            audio_storage_key=payload.audio_storage_key,
            audio_valid_for_mvp=payload.audio_valid_for_mvp,
            release_date=payload.release_date,
            fetched_at=payload.fetched_at,
        )
        self.session.add(track)
        await self.session.flush()
        await self.session.refresh(track)
        return track

    async def update_track(self, track: Track, payload: TrackUpsertDTO) -> Track:
        if payload.added_by_user_id is not None or track.added_by_user_id is None:
            track.added_by_user_id = payload.added_by_user_id
        track.service = payload.service
        track.title = payload.title
        track.duration = payload.duration
        track.duration_ms = payload.duration_ms
        track.external_url = payload.external_url
        track.cover_storage_key = payload.cover_storage_key
        track.audio_storage_key = payload.audio_storage_key
        track.audio_valid_for_mvp = payload.audio_valid_for_mvp
        track.release_date = payload.release_date
        track.fetched_at = payload.fetched_at
        await self.session.flush()
        await self.session.refresh(track)
        return track
