from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.yandex_service.databaseloder.dto import YandexTrackUpsertDTO
from database.models.models import YandexTrack


class YandexTrackRepos:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_yandex_track_id(self, yandex_track_id: str) -> YandexTrack | None:
        query = select(YandexTrack).where(YandexTrack.yandex_track_id == yandex_track_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def upsert_yandex_meta(self, track_id: int, payload: YandexTrackUpsertDTO) -> YandexTrack:
        existing = await self.get_by_yandex_track_id(payload.yandex_track_id)
        if existing is None:
            meta = YandexTrack(
                track_id=track_id,
                yandex_track_id=payload.yandex_track_id,
                yandex_album_id=payload.yandex_album_id,
                play_count=payload.play_count,
                likes_count=payload.likes_count,
                lyrics_available=payload.lyrics_available,
                lyrics_available_set=payload.lyrics_available_set,
                codec=payload.codec,
                bitrate_kbps=payload.bitrate_kbps,
                provider_fetched_at=payload.provider_fetched_at,
            )
            self.session.add(meta)
            await self.session.flush()
            await self.session.refresh(meta)
            return meta

        existing.track_id = track_id
        existing.yandex_album_id = payload.yandex_album_id
        existing.play_count = payload.play_count
        existing.likes_count = payload.likes_count
        existing.lyrics_available = payload.lyrics_available
        existing.lyrics_available_set = payload.lyrics_available_set
        existing.codec = payload.codec
        existing.bitrate_kbps = payload.bitrate_kbps
        existing.provider_fetched_at = payload.provider_fetched_at
        await self.session.flush()
        await self.session.refresh(existing)
        return existing
