import uuid
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.base import UserRole
from database.models.models import Connection, Group, GroupQr, Playlist, Track, User


class GroupRepos:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_group_by_id(self, group_id: uuid.UUID) -> Group | None:
        query = select(Group).where(Group.id == group_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_connection(self, user_id: uuid.UUID, group_id: uuid.UUID) -> Connection | None:
        query = select(Connection).where(
            Connection.user_id == user_id,
            Connection.group_id == group_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_user_groups(self, user_id: uuid.UUID) -> list[Group]:
        query = (
            select(Group)
            .join(Connection, Connection.group_id == Group.id)
            .where(Connection.user_id == user_id)
            .order_by(Group.name.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_group_playlists(self, group_id: uuid.UUID) -> list[tuple[Playlist, int]]:
        track_count = func.count(Track.id).label("track_count")
        query = (
            select(Playlist, track_count)
            .outerjoin(Track, Track.playlist_id == Playlist.id)
            .where(Playlist.group_id == group_id)
            .group_by(Playlist.id)
            .order_by(Playlist.id.asc())
        )
        result = await self.session.execute(query)
        return [(playlist, int(count)) for playlist, count in result.all()]

    async def list_group_users(self, group_id: uuid.UUID) -> list[tuple[User, UserRole]]:
        query = (
            select(User, Connection.role)
            .join(Connection, Connection.user_id == User.id)
            .where(Connection.group_id == group_id)
            .order_by(Connection.joined_at.asc())
        )
        result = await self.session.execute(query)
        return [(user, role) for user, role in result.all()]

    async def get_group_qr(self, group_id: uuid.UUID) -> GroupQr | None:
        query = select(GroupQr).where(GroupQr.group_id == group_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def upsert_group_qr(self, group_id: uuid.UUID) -> GroupQr:
        existing_qr = await self.get_group_qr(group_id)
        now = datetime.utcnow()
        expires_at = now + timedelta(days=7)

        if existing_qr:
            if existing_qr.expired_at > now:
                return existing_qr

            existing_qr.url = f"https://playlistpass.local/groups/{group_id}/join/{uuid.uuid4()}"
            existing_qr.expired_at = expires_at
            await self.session.commit()
            await self.session.refresh(existing_qr)
            return existing_qr

        qr = GroupQr(
            group_id=group_id,
            url=f"https://playlistpass.local/groups/{group_id}/join/{uuid.uuid4()}",
            expired_at=expires_at,
        )
        self.session.add(qr)
        await self.session.commit()
        await self.session.refresh(qr)
        return qr

    async def create_group(self, *, name: str, is_public: bool, owner_id: uuid.UUID) -> Group:
        group = Group(name=name, is_public=is_public)
        self.session.add(group)
        await self.session.flush()

        owner_connection = Connection(
            user_id=owner_id,
            group_id=group.id,
            role=UserRole.MAINTAINER,
        )
        self.session.add(owner_connection)
        await self.session.commit()
        await self.session.refresh(group)
        return group

    async def update_group(self, group: Group, *, name: str | None = None) -> Group:
        if name is not None:
            group.name = name
        await self.session.commit()
        await self.session.refresh(group)
        return group

    async def update_connection_role(
        self,
        *,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
        new_role: UserRole,
    ) -> Connection | None:
        connection = await self.get_user_connection(user_id=user_id, group_id=group_id)
        if connection is None:
            return None

        connection.role = new_role
        await self.session.commit()
        await self.session.refresh(connection)
        return connection

    async def delete_group(self, group_id: uuid.UUID) -> bool:
        group = await self.get_group_by_id(group_id)
        if group is None:
            return False

        playlist_ids_query = select(Playlist.id).where(Playlist.group_id == group_id)
        playlist_ids_result = await self.session.execute(playlist_ids_query)
        playlist_ids = list(playlist_ids_result.scalars().all())

        if playlist_ids:
            await self.session.execute(delete(Track).where(Track.playlist_id.in_(playlist_ids)))
            await self.session.execute(delete(Playlist).where(Playlist.id.in_(playlist_ids)))

        await self.session.execute(delete(GroupQr).where(GroupQr.group_id == group_id))
        await self.session.execute(delete(Connection).where(Connection.group_id == group_id))
        await self.session.execute(delete(Group).where(Group.id == group_id))
        await self.session.commit()
        return True
