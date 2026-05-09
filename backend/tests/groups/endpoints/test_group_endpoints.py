import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.base import StreamingService, UserRole
from database.models.models import Connection, Group, Playlist, PlaylistTrack, Track
from main import app
from routes.deps.storage_deps import get_storage_service
from services.storage.base import StorageServiceBase


pytestmark = pytest.mark.asyncio


async def register_user(
    *,
    client,
    email: str,
    name: str,
    password: str = "StrongPass123",
) -> dict:
    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "name": name,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def login_user(
    *,
    client,
    email: str,
    password: str = "StrongPass123",
) -> dict[str, str]:
    response = await client.post(
        "/auth/jwt/login",
        data={
            "username": email,
            "password": password,
        },
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def create_group(
    *,
    client,
    headers: dict[str, str],
    name: str,
    is_public: bool = True,
) -> dict:
    response = await client.post(
        "/groups/",
        headers=headers,
        json={"name": name, "is_public": is_public},
    )
    assert response.status_code == 201, response.text
    return response.json()


class FakeStorageService(StorageServiceBase):
    def __init__(self) -> None:
        super().__init__(bucket_name="test-bucket", presigned_url_ttl_seconds=600)
        self.objects: set[str] = set()
        self.object_bytes: dict[str, bytes] = {}

    async def create_object(self, *, object_key: str, data: bytes, content_type: str | None = None) -> None:
        self.objects.add(object_key)
        self.object_bytes[object_key] = data

    async def read_object(self, *, object_key: str) -> bytes:
        if object_key not in self.object_bytes:
            raise FileNotFoundError(object_key)
        return self.object_bytes[object_key]

    async def update_object(self, *, object_key: str, data: bytes, content_type: str | None = None) -> None:
        await self.create_object(object_key=object_key, data=data, content_type=content_type)

    async def delete_object(self, *, object_key: str) -> None:
        self.objects.discard(object_key)
        self.object_bytes.pop(object_key, None)

    async def object_exists(self, *, object_key: str) -> bool:
        return object_key in self.objects

    async def generate_presigned_upload_url(self, *, object_key: str, content_type: str | None = None) -> str:
        return f"https://upload.local/{object_key}"

    async def generate_presigned_download_url(self, *, object_key: str) -> str:
        return f"https://download.local/{object_key}"

    def build_public_url(self, *, object_key: str) -> str:
        return f"https://cdn.local/{object_key}"


@pytest.fixture
def fake_storage_service() -> FakeStorageService:
    return FakeStorageService()


@pytest.fixture
def override_storage_dependency(fake_storage_service: FakeStorageService):
    async def _override_storage_service() -> FakeStorageService:
        return fake_storage_service

    app.dependency_overrides[get_storage_service] = _override_storage_service
    try:
        yield fake_storage_service
    finally:
        app.dependency_overrides.pop(get_storage_service, None)


async def test_get_group_list_requires_auth(client) -> None:
    response = await client.get("/groups/")
    assert response.status_code == 401


async def test_create_group_returns_data_and_creates_maintainer_connection(client, db_session: AsyncSession) -> None:
    user = await register_user(client=client, email="owner@example.com", name="Owner")
    headers = await login_user(client=client, email="owner@example.com")

    created = await create_group(
        client=client,
        headers=headers,
        name="Integration Group",
        is_public=False,
    )

    assert created["name"] == "Integration Group"
    assert created["is_public"] is False
    assert created["image_url"] is None

    group_id = uuid.UUID(created["id"])
    user_id = uuid.UUID(user["id"])
    result = await db_session.execute(
        select(Connection).where(
            Connection.group_id == group_id,
            Connection.user_id == user_id,
        )
    )
    connection = result.scalar_one_or_none()
    assert connection is not None
    assert connection.role == UserRole.MAINTAINER


async def test_get_group_list_returns_only_current_user_groups(client) -> None:
    await register_user(client=client, email="u1@example.com", name="U1")
    headers_1 = await login_user(client=client, email="u1@example.com")
    await create_group(client=client, headers=headers_1, name="Alpha Group")
    await create_group(client=client, headers=headers_1, name="Beta Group")

    await register_user(client=client, email="u2@example.com", name="U2")
    headers_2 = await login_user(client=client, email="u2@example.com")
    await create_group(client=client, headers=headers_2, name="Gamma Group")

    response = await client.get("/groups/", headers=headers_1)
    assert response.status_code == 200

    names = [item["name"] for item in response.json()]
    assert names == ["Alpha Group", "Beta Group"]


async def test_get_group_users_requires_membership(client) -> None:
    await register_user(client=client, email="maint@example.com", name="Maint")
    maint_headers = await login_user(client=client, email="maint@example.com")
    group = await create_group(client=client, headers=maint_headers, name="Access Group")

    await register_user(client=client, email="outsider@example.com", name="Outsider")
    outsider_headers = await login_user(client=client, email="outsider@example.com")

    response = await client.get(f"/groups/{group['id']}/users", headers=outsider_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "GROUP_ACCESS_DENIED"


async def test_get_group_users_returns_roles_for_members(client, db_session: AsyncSession) -> None:
    maintainer = await register_user(client=client, email="member_m@example.com", name="Maintainer")
    maint_headers = await login_user(client=client, email="member_m@example.com")
    group = await create_group(client=client, headers=maint_headers, name="Members Group")

    guest = await register_user(client=client, email="member_g@example.com", name="Guest")
    db_session.add(
        Connection(
            user_id=uuid.UUID(guest["id"]),
            group_id=uuid.UUID(group["id"]),
            role=UserRole.GUEST,
        )
    )
    await db_session.commit()

    response = await client.get(f"/groups/{group['id']}/users", headers=maint_headers)
    assert response.status_code == 200

    users_by_email = {item["email"]: item for item in response.json()}
    assert users_by_email["member_m@example.com"]["role"] == "MAINTAINER"
    assert users_by_email["member_g@example.com"]["role"] == "GUEST"
    assert users_by_email["member_m@example.com"]["id"] == maintainer["id"]


async def test_get_group_playlist_returns_track_counts(client, db_session: AsyncSession) -> None:
    user = await register_user(client=client, email="tracks@example.com", name="Tracks User")
    headers = await login_user(client=client, email="tracks@example.com")
    group = await create_group(client=client, headers=headers, name="Playlist Group")

    playlist = Playlist(
        group_id=uuid.UUID(group["id"]),
        name="Stored Playlist Name",
        image_url="https://example.com/cover.jpg",
    )
    db_session.add(playlist)
    await db_session.flush()

    track_one = Track(
        added_by_user_id=uuid.UUID(user["id"]),
        service=StreamingService.SPOTIFY,
        title="Track One",
        duration=200,
        external_url="https://example.com/tracks/1",
        audio_storage_key="tracks/audio-1.mp3",
    )
    track_two = Track(
        added_by_user_id=uuid.UUID(user["id"]),
        service=StreamingService.SPOTIFY,
        title="Track Two",
        duration=180,
        external_url="https://example.com/tracks/2",
        audio_storage_key="tracks/audio-2.mp3",
    )
    db_session.add_all([track_one, track_two])
    await db_session.flush()
    db_session.add_all(
        [
            PlaylistTrack(playlist_id=playlist.id, track_id=track_one.id),
            PlaylistTrack(playlist_id=playlist.id, track_id=track_two.id),
        ]
    )
    await db_session.commit()

    response = await client.get(f"/groups/{group['id']}/playlists", headers=headers)
    assert response.status_code == 200

    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["track_count"] == 2
    assert payload[0]["name"] == "Stored Playlist Name"
    assert payload[0]["image_url"] == "https://example.com/cover.jpg"


async def test_get_group_playlist_allows_shared_track_between_playlists(
    client,
    db_session: AsyncSession,
) -> None:
    user = await register_user(client=client, email="shared@example.com", name="Shared User")
    headers = await login_user(client=client, email="shared@example.com")
    group = await create_group(client=client, headers=headers, name="Shared Track Group")

    playlist_a = Playlist(
        group_id=uuid.UUID(group["id"]),
        name="Playlist A",
        image_url=None,
    )
    playlist_b = Playlist(
        group_id=uuid.UUID(group["id"]),
        name="Playlist B",
        image_url=None,
    )
    db_session.add_all([playlist_a, playlist_b])
    await db_session.flush()

    shared_track = Track(
        added_by_user_id=uuid.UUID(user["id"]),
        service=StreamingService.SPOTIFY,
        title="Shared Track",
        duration=210,
        external_url="https://example.com/tracks/shared",
        audio_storage_key="tracks/shared.mp3",
    )
    extra_track = Track(
        added_by_user_id=uuid.UUID(user["id"]),
        service=StreamingService.SPOTIFY,
        title="Extra Track",
        duration=190,
        external_url="https://example.com/tracks/extra",
        audio_storage_key="tracks/extra.mp3",
    )
    db_session.add_all([shared_track, extra_track])
    await db_session.flush()

    db_session.add_all(
        [
            PlaylistTrack(playlist_id=playlist_a.id, track_id=shared_track.id),
            PlaylistTrack(playlist_id=playlist_a.id, track_id=extra_track.id),
            PlaylistTrack(playlist_id=playlist_b.id, track_id=shared_track.id),
        ]
    )
    await db_session.commit()

    response = await client.get(f"/groups/{group['id']}/playlists", headers=headers)
    assert response.status_code == 200

    payload = {item["name"]: item["track_count"] for item in response.json()}
    assert payload["Playlist A"] == 2
    assert payload["Playlist B"] == 1


async def test_get_group_qr_returns_same_qr_while_not_expired(client) -> None:
    await register_user(client=client, email="qr@example.com", name="Qr User")
    headers = await login_user(client=client, email="qr@example.com")
    group = await create_group(client=client, headers=headers, name="Qr Group")

    first = await client.get(f"/groups/{group['id']}/qr", headers=headers)
    second = await client.get(f"/groups/{group['id']}/qr", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["group_id"] == group["id"]
    assert second.json()["group_id"] == group["id"]
    assert first.json()["qr_url"] == second.json()["qr_url"]


async def test_update_group_info_requires_maintainer(client, db_session: AsyncSession) -> None:
    await register_user(client=client, email="up_maint@example.com", name="Maint")
    maint_headers = await login_user(client=client, email="up_maint@example.com")
    group = await create_group(client=client, headers=maint_headers, name="Rename Group")

    guest = await register_user(client=client, email="up_guest@example.com", name="Guest")
    guest_headers = await login_user(client=client, email="up_guest@example.com")
    db_session.add(
        Connection(
            user_id=uuid.UUID(guest["id"]),
            group_id=uuid.UUID(group["id"]),
            role=UserRole.GUEST,
        )
    )
    await db_session.commit()

    forbidden = await client.patch(
        f"/groups/{group['id']}",
        headers=guest_headers,
        json={"name": "Should Not Work"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == "GROUP_MAINTAINER_REQUIRED"

    success = await client.patch(
        f"/groups/{group['id']}",
        headers=maint_headers,
        json={"name": "Renamed Group"},
    )
    assert success.status_code == 200
    assert success.json()["name"] == "Renamed Group"


async def test_group_image_upload_init_returns_presigned_payload(
    client,
    override_storage_dependency: FakeStorageService,
) -> None:
    await register_user(client=client, email="img_owner@example.com", name="Owner")
    headers = await login_user(client=client, email="img_owner@example.com")
    group = await create_group(client=client, headers=headers, name="Image Group")

    response = await client.post(
        f"/groups/{group['id']}/image/upload-init",
        headers=headers,
        json={"filename": "cover.jpg", "content_type": "image/jpeg"},
    )
    assert response.status_code == 200, response.text

    payload = response.json()
    expected_prefix = f"groups/{group['id']}/"
    assert payload["object_key"].startswith(expected_prefix)
    assert payload["upload_url"] == f"https://upload.local/{payload['object_key']}"
    assert payload["file_url"] == f"https://cdn.local/{payload['object_key']}"
    assert payload["expires_in_seconds"] == 600


async def test_group_image_upload_init_rejects_unsupported_format(
    client,
    override_storage_dependency: FakeStorageService,
) -> None:
    await register_user(client=client, email="img_invalid@example.com", name="Owner")
    headers = await login_user(client=client, email="img_invalid@example.com")
    group = await create_group(client=client, headers=headers, name="Image Invalid Group")

    response = await client.post(
        f"/groups/{group['id']}/image/upload-init",
        headers=headers,
        json={"filename": "cover.gif", "content_type": "image/gif"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "GROUP_IMAGE_UNSUPPORTED_FORMAT"


async def test_group_image_commit_saves_group_image_url(
    client,
    db_session: AsyncSession,
    override_storage_dependency: FakeStorageService,
) -> None:
    await register_user(client=client, email="img_commit@example.com", name="Owner")
    headers = await login_user(client=client, email="img_commit@example.com")
    group = await create_group(client=client, headers=headers, name="Image Commit Group")

    init_response = await client.post(
        f"/groups/{group['id']}/image/upload-init",
        headers=headers,
        json={"filename": "cover.png", "content_type": "image/png"},
    )
    assert init_response.status_code == 200, init_response.text
    object_key = init_response.json()["object_key"]
    override_storage_dependency.objects.add(object_key)

    commit_response = await client.post(
        f"/groups/{group['id']}/image/commit",
        headers=headers,
        json={"object_key": object_key},
    )
    assert commit_response.status_code == 200, commit_response.text
    payload = commit_response.json()
    expected_url = f"https://cdn.local/{object_key}"
    assert payload["image_url"] == expected_url

    group_row = await db_session.execute(
        select(Group).where(Group.id == uuid.UUID(group["id"]))
    )
    stored_group = group_row.scalar_one()
    assert stored_group.image_url == expected_url


async def test_group_image_commit_returns_not_found_for_missing_object(
    client,
    override_storage_dependency: FakeStorageService,
) -> None:
    await register_user(client=client, email="img_missing@example.com", name="Owner")
    headers = await login_user(client=client, email="img_missing@example.com")
    group = await create_group(client=client, headers=headers, name="Image Missing Group")

    response = await client.post(
        f"/groups/{group['id']}/image/commit",
        headers=headers,
        json={"object_key": f"groups/{group['id']}/missing.jpg"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "GROUP_IMAGE_OBJECT_NOT_FOUND"


async def test_group_image_delete_clears_db_field_and_storage_object(
    client,
    db_session: AsyncSession,
    override_storage_dependency: FakeStorageService,
) -> None:
    await register_user(client=client, email="img_delete@example.com", name="Owner")
    headers = await login_user(client=client, email="img_delete@example.com")
    group = await create_group(client=client, headers=headers, name="Image Delete Group")

    init_response = await client.post(
        f"/groups/{group['id']}/image/upload-init",
        headers=headers,
        json={"filename": "cover.webp", "content_type": "image/webp"},
    )
    object_key = init_response.json()["object_key"]
    override_storage_dependency.objects.add(object_key)

    commit_response = await client.post(
        f"/groups/{group['id']}/image/commit",
        headers=headers,
        json={"object_key": object_key},
    )
    assert commit_response.status_code == 200, commit_response.text
    assert object_key in override_storage_dependency.objects

    delete_response = await client.delete(
        f"/groups/{group['id']}/image",
        headers=headers,
    )
    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json()["status"] == "deleted"
    assert delete_response.json()["group_id"] == group["id"]
    assert object_key not in override_storage_dependency.objects

    group_row = await db_session.execute(
        select(Group).where(Group.id == uuid.UUID(group["id"]))
    )
    stored_group = group_row.scalar_one()
    assert stored_group.image_url is None


async def test_change_group_user_role_updates_target_member(client, db_session: AsyncSession) -> None:
    await register_user(client=client, email="role_owner@example.com", name="Owner")
    owner_headers = await login_user(client=client, email="role_owner@example.com")
    group = await create_group(client=client, headers=owner_headers, name="Roles Group")

    member = await register_user(client=client, email="role_member@example.com", name="Member")
    db_session.add(
        Connection(
            user_id=uuid.UUID(member["id"]),
            group_id=uuid.UUID(group["id"]),
            role=UserRole.GUEST,
        )
    )
    await db_session.commit()

    response = await client.patch(
        f"/groups/{group['id']}/users/{member['id']}/role",
        headers=owner_headers,
        json={"role": "VIEWER"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "VIEWER"

    updated = await db_session.execute(
        select(Connection).where(
            Connection.group_id == uuid.UUID(group["id"]),
            Connection.user_id == uuid.UUID(member["id"]),
        )
    )
    connection = updated.scalar_one()
    assert connection.role == UserRole.VIEWER


async def test_change_group_user_role_cannot_change_maintainer(client) -> None:
    owner = await register_user(client=client, email="self_owner@example.com", name="Owner")
    owner_headers = await login_user(client=client, email="self_owner@example.com")
    group = await create_group(client=client, headers=owner_headers, name="Maintainers Group")

    response = await client.patch(
        f"/groups/{group['id']}/users/{owner['id']}/role",
        headers=owner_headers,
        json={"role": "VIEWER"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "GROUP_CANNOT_CHANGE_MAINTAINER_ROLE"


async def test_delete_group_marks_resource_deleted(client, db_session: AsyncSession) -> None:
    await register_user(client=client, email="delete_owner@example.com", name="Owner")
    headers = await login_user(client=client, email="delete_owner@example.com")
    group = await create_group(client=client, headers=headers, name="Delete Me")

    response = await client.delete(f"/groups/{group['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    assert response.json()["group_id"] == group["id"]

    result = await db_session.execute(select(Group).where(Group.id == uuid.UUID(group["id"])))
    assert result.scalar_one_or_none() is None
