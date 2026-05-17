import uuid
from datetime import datetime
from urllib.parse import urlparse

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from database.models.base import UserRole
from database.models.models import Connection, Group, User
from database.repos.group_repos import GroupRepos
from schemas.group import (
    GroupCreateRequest,
    GroupImageCommitRequest,
    GroupImageDeleteResponse,
    GroupImageUploadInitRequest,
    GroupImageUploadInitResponse,
    GroupListItemResponse,
    GroupPlaylistItemResponse,
    GroupQrResponse,
    GroupUpdateRequest,
    GroupUserItemResponse,
    GroupUserRoleUpdateRequest,
)
from services.storage.base import InvalidStorageFormatError, StorageServiceBase
from services.storage.types import StorageEntity, StorageFileFormat, StorageObjectDescriptor


CONTENT_TYPE_TO_IMAGE_FORMAT: dict[str, StorageFileFormat] = {
    "image/jpg": StorageFileFormat.JPG,
    "image/jpeg": StorageFileFormat.JPEG,
    "image/pjpeg": StorageFileFormat.JPEG,
    "image/png": StorageFileFormat.PNG,
    "image/x-png": StorageFileFormat.PNG,
    "image/webp": StorageFileFormat.WEBP,
}


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

    async def get_track_editor_connection_or_403(self, *, user: User, group: Group) -> Connection:
        connection = await self.get_member_connection_or_403(user=user, group=group)
        if connection.role == UserRole.VIEWER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="GROUP_TRACK_EDIT_FORBIDDEN",
            )
        return connection

    async def get_group_list(self, *, user: User) -> list[GroupListItemResponse]:
        groups = await self.repos.list_user_groups(user_id=user.id)
        return [
            GroupListItemResponse(
                id=group.id,
                name=group.name,
                image_url=group.image_url,
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
                name=playlist.name,
                image_url=playlist.image_url,
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
            image_url=group.image_url,
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
            image_url=updated_group.image_url,
            is_public=updated_group.is_public,
        )

    async def init_group_image_upload(
        self,
        *,
        user: User,
        group: Group,
        payload: GroupImageUploadInitRequest,
        storage_service: StorageServiceBase,
    ) -> GroupImageUploadInitResponse:
        await self.get_maintainer_connection_or_403(user=user, group=group)

        file_format = self._resolve_group_image_format(
            filename=payload.filename,
            content_type=payload.content_type,
        )
        descriptor = StorageObjectDescriptor(
            entity=StorageEntity.GROUP,
            file_format=file_format,
            entity_id=group.id,
            filename=self._strip_filename_extension(payload.filename),
        )

        try:
            object_key = storage_service.build_object_key(descriptor)
        except InvalidStorageFormatError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GROUP_IMAGE_UNSUPPORTED_FORMAT",
            ) from error

        try:
            upload_url = await storage_service.generate_presigned_upload_url(
                object_key=object_key,
                content_type=payload.content_type,
            )
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="STORAGE_BACKEND_NOT_AVAILABLE",
            ) from error
        file_url = storage_service.build_public_url(object_key=object_key)
        return GroupImageUploadInitResponse(
            object_key=object_key,
            upload_url=upload_url,
            file_url=file_url,
            expires_in_seconds=storage_service.presigned_url_ttl_seconds,
        )

    async def commit_group_image_upload(
        self,
        *,
        user: User,
        group: Group,
        payload: GroupImageCommitRequest,
        storage_service: StorageServiceBase,
    ) -> GroupListItemResponse:
        await self.get_maintainer_connection_or_403(user=user, group=group)

        object_key = payload.object_key.strip().lstrip("/")
        if not self._is_group_object_key(group_id=group.id, object_key=object_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GROUP_IMAGE_OBJECT_KEY_INVALID",
            )

        try:
            object_exists = await storage_service.object_exists(object_key=object_key)
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="STORAGE_BACKEND_NOT_AVAILABLE",
            ) from error
        if not object_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GROUP_IMAGE_OBJECT_NOT_FOUND",
            )

        previous_object_key = self._extract_object_key_from_stored_value(
            group.image_url,
            bucket_name=storage_service.bucket_name,
        )
        image_url = (
            payload.image_url.strip()
            if payload.image_url and payload.image_url.strip()
            else storage_service.build_public_url(object_key=object_key)
        )
        updated_group = await self.repos.update_group_image(group, image_url=image_url)

        if previous_object_key and previous_object_key != object_key:
            try:
                await storage_service.delete_object(object_key=previous_object_key)
            except Exception:
                # Cleanup is best-effort and should not break successful image replacement.
                pass

        return GroupListItemResponse(
            id=updated_group.id,
            name=updated_group.name,
            image_url=updated_group.image_url,
            is_public=updated_group.is_public,
        )

    async def delete_group_image(
        self,
        *,
        user: User,
        group: Group,
        storage_service: StorageServiceBase,
    ) -> GroupImageDeleteResponse:
        await self.get_maintainer_connection_or_403(user=user, group=group)

        object_key = self._extract_object_key_from_stored_value(
            group.image_url,
            bucket_name=storage_service.bucket_name,
        )
        if object_key:
            try:
                await storage_service.delete_object(object_key=object_key)
            except Exception:
                # Cleanup is best-effort and should not block unlinking an image in DB.
                pass

        await self.repos.update_group_image(group, image_url=None)
        return GroupImageDeleteResponse(group_id=group.id)

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

    @staticmethod
    def _resolve_group_image_format(*, filename: str, content_type: str | None) -> StorageFileFormat:
        filename_format = GroupManager._extract_format_from_filename(filename)
        content_type_format = GroupManager._extract_format_from_content_type(content_type)

        if (
            filename_format
            and content_type_format
            and GroupManager._normalize_image_format(filename_format)
            != GroupManager._normalize_image_format(content_type_format)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GROUP_IMAGE_FORMAT_MISMATCH",
            )

        selected_format = filename_format or content_type_format
        if selected_format is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GROUP_IMAGE_UNSUPPORTED_FORMAT",
            )
        return selected_format

    @staticmethod
    def _extract_format_from_filename(filename: str) -> StorageFileFormat | None:
        if "." not in filename:
            return None
        extension = filename.rsplit(".", maxsplit=1)[-1].lower()
        try:
            return StorageFileFormat(extension)
        except ValueError:
            return None

    @staticmethod
    def _extract_format_from_content_type(content_type: str | None) -> StorageFileFormat | None:
        if not content_type:
            return None
        normalized = content_type.split(";", maxsplit=1)[0].strip().lower()
        return CONTENT_TYPE_TO_IMAGE_FORMAT.get(normalized)

    @staticmethod
    def _normalize_image_format(image_format: StorageFileFormat) -> StorageFileFormat:
        if image_format == StorageFileFormat.JPG:
            return StorageFileFormat.JPEG
        return image_format

    @staticmethod
    def _strip_filename_extension(filename: str) -> str:
        if "." not in filename:
            return filename
        return filename.rsplit(".", maxsplit=1)[0]

    @staticmethod
    def _is_group_object_key(*, group_id: uuid.UUID, object_key: str) -> bool:
        expected_prefix = f"{StorageEntity.GROUP.value}/{group_id}/"
        return object_key.startswith(expected_prefix)

    @staticmethod
    def _extract_object_key_from_stored_value(
        stored_value: str | None,
        *,
        bucket_name: str,
    ) -> str | None:
        if not stored_value:
            return None

        cleaned = stored_value.strip().lstrip("/")
        if not cleaned:
            return None
        if cleaned.startswith(f"{StorageEntity.GROUP.value}/"):
            return cleaned

        parsed = urlparse(cleaned)
        path = parsed.path.lstrip("/")
        if not path:
            return None

        bucket_prefix = f"{bucket_name.strip('/')}/"
        if path.startswith(bucket_prefix):
            return path[len(bucket_prefix):]
        group_path_marker = f"{StorageEntity.GROUP.value}/"
        marker_index = path.find(group_path_marker)
        if marker_index >= 0:
            return path[marker_index:]
        return path
