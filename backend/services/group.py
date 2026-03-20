import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from database.models.base import UserRole
from database.models.models import Connection, Group, User
from database.repos.group_repos import GroupRepos
from schemas.group import (
    GroupCreateRequest,
    GroupListItemResponse,
    GroupPlaylistItemResponse,
    GroupQrResponse,
    GroupUpdateRequest,
    GroupUserItemResponse,
    GroupUserRoleUpdateRequest,
)


class GroupManager:
    def __init__(self, repos: GroupRepos) -> None:
        self.repos = repos

    async def get_group_or_404(self, group_id: uuid.UUID) -> Group:
        group = await self.repos.get_group_by_id(group_id)
        if group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GROUP_NOT_FOUND",
            )
        return group

    async def get_member_connection_or_403(self, *, user: User, group: Group) -> Connection:
        connection = await self.repos.get_user_connection(user_id=user.id, group_id=group.id)
        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="GROUP_ACCESS_DENIED",
            )
        return connection

    async def get_maintainer_connection_or_403(self, *, user: User, group: Group) -> Connection:
        connection = await self.get_member_connection_or_403(user=user, group=group)
        if connection.role != UserRole.MAINTAINER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="GROUP_MAINTAINER_REQUIRED",
            )
        return connection

    async def get_group_list(self, *, user: User) -> list[GroupListItemResponse]:
        groups = await self.repos.list_user_groups(user_id=user.id)
        return [
            GroupListItemResponse(
                id=group.id,
                name=group.name,
                image_url=None,
                is_public=group.is_public,
            )
            for group in groups
        ]

    async def get_group_playlist(self, *, user: User, group: Group) -> list[GroupPlaylistItemResponse]:
        await self.get_member_connection_or_403(user=user, group=group)
        playlists_with_counts = await self.repos.list_group_playlists(group_id=group.id)

        return [
            GroupPlaylistItemResponse(
                id=playlist.id,
                name=f"Playlist {playlist.id}",
                image_url=None,
                track_count=track_count,
            )
            for playlist, track_count in playlists_with_counts
        ]

    async def get_group_qr(self, *, user: User, group: Group) -> GroupQrResponse:
        await self.get_member_connection_or_403(user=user, group=group)
        qr = await self.repos.upsert_group_qr(group_id=group.id)
        return GroupQrResponse(
            group_id=group.id,
            qr_url=qr.url,
            expired_at=qr.expired_at,
            is_expired=qr.expired_at <= datetime.utcnow(),
        )

    async def get_group_users(self, *, user: User, group: Group) -> list[GroupUserItemResponse]:
        await self.get_member_connection_or_403(user=user, group=group)
        users_and_roles = await self.repos.list_group_users(group_id=group.id)
        return [
            GroupUserItemResponse(
                id=member.id,
                email=member.email,
                name=member.name,
                role=role,
            )
            for member, role in users_and_roles
        ]

    async def create_group(self, *, user: User, payload: GroupCreateRequest) -> GroupListItemResponse:
        try:
            group = await self.repos.create_group(
                name=payload.name,
                is_public=payload.is_public,
                owner_id=user.id,
            )
        except IntegrityError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="GROUP_NAME_ALREADY_EXISTS",
            ) from error

        return GroupListItemResponse(
            id=group.id,
            name=group.name,
            image_url=None,
            is_public=group.is_public,
        )

    async def update_group_info(
        self,
        *,
        user: User,
        group: Group,
        payload: GroupUpdateRequest,
    ) -> GroupListItemResponse:
        await self.get_maintainer_connection_or_403(user=user, group=group)

        if payload.image_url is not None:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="GROUP_IMAGE_STORAGE_NOT_IMPLEMENTED",
            )

        try:
            updated_group = await self.repos.update_group(group, name=payload.name)
        except IntegrityError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="GROUP_NAME_ALREADY_EXISTS",
            ) from error

        return GroupListItemResponse(
            id=updated_group.id,
            name=updated_group.name,
            image_url=None,
            is_public=updated_group.is_public,
        )

    async def change_group_user_list(
        self,
        *,
        user: User,
        group: Group,
        target_user_id: uuid.UUID,
        payload: GroupUserRoleUpdateRequest,
    ) -> GroupUserItemResponse:
        await self.get_maintainer_connection_or_403(user=user, group=group)

        target_connection = await self.repos.get_user_connection(user_id=target_user_id, group_id=group.id)
        if target_connection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GROUP_USER_NOT_FOUND",
            )

        if target_connection.role == UserRole.MAINTAINER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GROUP_CANNOT_CHANGE_MAINTAINER_ROLE",
            )

        updated_connection = await self.repos.update_connection_role(
            group_id=group.id,
            user_id=target_user_id,
            new_role=payload.as_user_role,
        )
        if updated_connection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GROUP_USER_NOT_FOUND",
            )

        users_and_roles = await self.repos.list_group_users(group_id=group.id)
        for member, role in users_and_roles:
            if member.id == target_user_id:
                return GroupUserItemResponse(
                    id=member.id,
                    email=member.email,
                    name=member.name,
                    role=role,
                )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GROUP_USER_NOT_FOUND",
        )

    async def delete_group(self, *, user: User, group: Group) -> None:
        await self.get_maintainer_connection_or_403(user=user, group=group)
        deleted = await self.repos.delete_group(group_id=group.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GROUP_NOT_FOUND",
            )
