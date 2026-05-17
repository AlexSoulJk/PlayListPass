import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.base import StreamingService, UserRole
from database.models.models import Connection, Group, Playlist, PlaylistTrack, Track, TrackServiceLink
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


async def test_create_playlist_creates_playlist_for_maintainer(client, db_session: AsyncSession) -> None:
    await register_user(client=client, email="playlist_owner@example.com", name="Playlist Owner")
    headers = await login_user(client=client, email="playlist_owner@example.com")
    group = await create_group(client=client, headers=headers, name="Playlist Create Group")

    response = await client.post(
        f"/playlist/{group['id']}/create",
        headers=headers,
        json={"name": "Fresh Playlist", "image_url": "https://example.com/p-cover.jpg"},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["name"] == "Fresh Playlist"
    assert payload["image_url"] == "https://example.com/p-cover.jpg"

    playlist_row = await db_session.execute(
        select(Playlist).where(Playlist.id == uuid.UUID(payload["id"]))
    )
    stored_playlist = playlist_row.scalar_one_or_none()
    assert stored_playlist is not None
    assert stored_playlist.group_id == uuid.UUID(group["id"])


async def test_create_playlist_requires_maintainer_role(client, db_session: AsyncSession) -> None:
    await register_user(client=client, email="playlist_main@example.com", name="Playlist Main")
    owner_headers = await login_user(client=client, email="playlist_main@example.com")
    group = await create_group(client=client, headers=owner_headers, name="Playlist Access Group")

    guest = await register_user(client=client, email="playlist_guest@example.com", name="Playlist Guest")
    guest_headers = await login_user(client=client, email="playlist_guest@example.com")
    db_session.add(
        Connection(
            user_id=uuid.UUID(guest["id"]),
            group_id=uuid.UUID(group["id"]),
            role=UserRole.GUEST,
        )
    )
    await db_session.commit()

    response = await client.post(
        f"/playlist/{group['id']}/create",
        headers=guest_headers,
        json={"name": "Should Not Be Created"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "GROUP_MAINTAINER_REQUIRED"


async def test_create_playlist_rejects_duplicate_name_in_group(client) -> None:
    await register_user(client=client, email="playlist_dup@example.com", name="Playlist Dup")
    headers = await login_user(client=client, email="playlist_dup@example.com")
    group = await create_group(client=client, headers=headers, name="Playlist Duplicate Group")

    first = await client.post(
        f"/playlist/{group['id']}/create",
        headers=headers,
        json={"name": "Duplicate Playlist"},
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        f"/playlist/{group['id']}/create",
        headers=headers,
        json={"name": " duplicate playlist "},
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "PLAYLIST_NAME_ALREADY_EXISTS"


async def test_delete_playlist_deletes_record_and_storage_object(
    client,
    db_session: AsyncSession,
    override_storage_dependency: FakeStorageService,
) -> None:
    await register_user(client=client, email="playlist_delete_owner@example.com", name="Playlist Delete Owner")
    headers = await login_user(client=client, email="playlist_delete_owner@example.com")
    group = await create_group(client=client, headers=headers, name="Playlist Delete Group")

    storage_object_key = "playlists/manual-cover-id/cover.jpg"
    created_response = await client.post(
        f"/playlist/{group['id']}/create",
        headers=headers,
        json={
            "name": "Playlist To Delete",
            "image_url": f"https://cdn.local/{storage_object_key}",
        },
    )
    assert created_response.status_code == 201, created_response.text
    playlist_id = created_response.json()["id"]
    override_storage_dependency.objects.add(storage_object_key)

    delete_response = await client.delete(
        f"/playlist/{group['id']}/{playlist_id}",
        headers=headers,
    )
    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json()["status"] == "deleted"
    assert delete_response.json()["playlist_id"] == playlist_id
    assert storage_object_key not in override_storage_dependency.objects

    playlist_row = await db_session.execute(
        select(Playlist).where(Playlist.id == uuid.UUID(playlist_id))
    )
    assert playlist_row.scalar_one_or_none() is None


async def test_delete_playlist_requires_maintainer(client, db_session: AsyncSession) -> None:
    await register_user(client=client, email="playlist_delete_main@example.com", name="Playlist Delete Main")
    owner_headers = await login_user(client=client, email="playlist_delete_main@example.com")
    group = await create_group(client=client, headers=owner_headers, name="Playlist Delete Access Group")

    created_response = await client.post(
        f"/playlist/{group['id']}/create",
        headers=owner_headers,
        json={"name": "Playlist Protected Delete"},
    )
    assert created_response.status_code == 201, created_response.text
    playlist_id = created_response.json()["id"]

    guest = await register_user(client=client, email="playlist_delete_guest@example.com", name="Playlist Delete Guest")
    guest_headers = await login_user(client=client, email="playlist_delete_guest@example.com")
    db_session.add(
        Connection(
            user_id=uuid.UUID(guest["id"]),
            group_id=uuid.UUID(group["id"]),
            role=UserRole.GUEST,
        )
    )
    await db_session.commit()

    response = await client.delete(
        f"/playlist/{group['id']}/{playlist_id}",
        headers=guest_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "GROUP_MAINTAINER_REQUIRED"


async def test_delete_playlist_returns_not_found_for_unknown_playlist(client) -> None:
    await register_user(client=client, email="playlist_delete_nf@example.com", name="Playlist Delete NF")
    headers = await login_user(client=client, email="playlist_delete_nf@example.com")
    group = await create_group(client=client, headers=headers, name="Playlist Delete Not Found Group")

    response = await client.delete(
        f"/playlist/{group['id']}/{uuid.uuid4()}",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "PLAYLIST_NOT_FOUND"


async def test_update_playlist_updates_name_for_maintainer(client, db_session: AsyncSession) -> None:
    await register_user(client=client, email="playlist_upd@example.com", name="Playlist Upd")
    headers = await login_user(client=client, email="playlist_upd@example.com")
    group = await create_group(client=client, headers=headers, name="Playlist Update Group")

    created = await client.post(
        f"/playlist/{group['id']}/create",
        headers=headers,
        json={"name": "Initial Playlist"},
    )
    assert created.status_code == 201, created.text
    playlist_id = created.json()["id"]

    response = await client.patch(
        f"/playlist/{group['id']}/{playlist_id}",
        headers=headers,
        json={"name": "Updated Playlist"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Updated Playlist"

    playlist_row = await db_session.execute(
        select(Playlist).where(Playlist.id == uuid.UUID(playlist_id))
    )
    stored_playlist = playlist_row.scalar_one()
    assert stored_playlist.name == "Updated Playlist"


async def test_update_playlist_rejects_duplicate_name(client) -> None:
    await register_user(client=client, email="playlist_upd_dup@example.com", name="Playlist Upd Dup")
    headers = await login_user(client=client, email="playlist_upd_dup@example.com")
    group = await create_group(client=client, headers=headers, name="Playlist Update Duplicate Group")

    first = await client.post(
        f"/playlist/{group['id']}/create",
        headers=headers,
        json={"name": "One"},
    )
    second = await client.post(
        f"/playlist/{group['id']}/create",
        headers=headers,
        json={"name": "Two"},
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    response = await client.patch(
        f"/playlist/{group['id']}/{second.json()['id']}",
        headers=headers,
        json={"name": " one "},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "PLAYLIST_NAME_ALREADY_EXISTS"


async def test_playlist_image_upload_commit_and_delete_flow(
    client,
    db_session: AsyncSession,
    override_storage_dependency: FakeStorageService,
) -> None:
    await register_user(client=client, email="playlist_img@example.com", name="Playlist Img")
    headers = await login_user(client=client, email="playlist_img@example.com")
    group = await create_group(client=client, headers=headers, name="Playlist Image Group")

    create_response = await client.post(
        f"/playlist/{group['id']}/create",
        headers=headers,
        json={"name": "Playlist With Image"},
    )
    assert create_response.status_code == 201, create_response.text
    playlist_id = create_response.json()["id"]

    init_response = await client.post(
        f"/playlist/{group['id']}/{playlist_id}/image/upload-init",
        headers=headers,
        json={"filename": "cover.jpg", "content_type": "image/jpeg"},
    )
    assert init_response.status_code == 200, init_response.text

    init_payload = init_response.json()
    expected_prefix = f"playlists/{playlist_id}/"
    assert init_payload["object_key"].startswith(expected_prefix)
    assert init_payload["upload_url"] == f"https://upload.local/{init_payload['object_key']}"
    assert init_payload["file_url"] == f"https://cdn.local/{init_payload['object_key']}"

    object_key = init_payload["object_key"]
    override_storage_dependency.objects.add(object_key)

    commit_response = await client.post(
        f"/playlist/{group['id']}/{playlist_id}/image/commit",
        headers=headers,
        json={"object_key": object_key},
    )
    assert commit_response.status_code == 200, commit_response.text
    assert commit_response.json()["image_url"] == f"https://cdn.local/{object_key}"

    playlist_row = await db_session.execute(
        select(Playlist).where(Playlist.id == uuid.UUID(playlist_id))
    )
    stored_playlist = playlist_row.scalar_one()
    assert stored_playlist.image_url == f"https://cdn.local/{object_key}"

    delete_response = await client.delete(
        f"/playlist/{group['id']}/{playlist_id}/image",
        headers=headers,
    )
    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json()["status"] == "deleted"
    assert delete_response.json()["playlist_id"] == playlist_id
    assert object_key not in override_storage_dependency.objects

    playlist_row_after_delete = await db_session.execute(
        select(Playlist).where(Playlist.id == uuid.UUID(playlist_id))
    )
    stored_playlist_after_delete = playlist_row_after_delete.scalar_one()
    assert stored_playlist_after_delete.image_url is None


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


async def test_search_tracks_returns_pagination_and_db_marker(
    client,
    db_session: AsyncSession,
    override_storage_dependency: FakeStorageService,
) -> None:
    user = await register_user(client=client, email="search_owner@example.com", name="Search Owner")
    headers = await login_user(client=client, email="search_owner@example.com")
    group = await create_group(client=client, headers=headers, name="Search Group")

    track = Track(
        added_by_user_id=uuid.UUID(user["id"]),
        service=StreamingService.SPOTIFY,
        title="Disturbia",
        duration=239,
        external_url="https://example.com/tracks/disturbia",
        cover_storage_key="tracks/covers/disturbia.jpg",
        audio_storage_key=None,
    )
    db_session.add(track)
    await db_session.flush()
    db_session.add(
        TrackServiceLink(
            track_id=track.id,
            service=StreamingService.SPOTIFY,
            service_track_id="spotify-123",
            external_url="https://open.spotify.com/track/spotify-123",
            cover_url="https://cdn.example.com/spotify-123.jpg",
            duration_sec=239,
            imported_from_search=True,
        )
    )
    await db_session.commit()

    response = await client.post(
        "/search/tracks",
        headers=headers,
        json={
            "group_id": group["id"],
            "query": "disturbia",
            "services": ["SPOTIFY", "YANDEX_MUSIC"],
            "page": 1,
            "page_size": 8,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["pagination"]["total"] == 1
    assert payload["pagination"]["page_size"] == 8
    assert payload["service_availability"]["YANDEX_MUSIC"] is True
    assert payload["service_availability"]["SPOTIFY"] is False
    assert payload["items"][0]["internal_track_id"] == track.id
    assert payload["items"][0]["is_in_db"] is True
    assert payload["items"][0]["service_track_id"] == "spotify-123"


async def test_add_track_to_playlist_allows_guest_with_internal_track(client, db_session: AsyncSession) -> None:
    owner = await register_user(client=client, email="add_track_owner@example.com", name="Owner")
    owner_headers = await login_user(client=client, email="add_track_owner@example.com")
    group = await create_group(client=client, headers=owner_headers, name="Add Track Group")

    create_playlist_response = await client.post(
        f"/playlist/{group['id']}/create",
        headers=owner_headers,
        json={"name": "Guest Editable Playlist"},
    )
    assert create_playlist_response.status_code == 201, create_playlist_response.text
    playlist_id = create_playlist_response.json()["id"]

    guest = await register_user(client=client, email="add_track_guest@example.com", name="Guest")
    guest_headers = await login_user(client=client, email="add_track_guest@example.com")
    db_session.add(
        Connection(
            user_id=uuid.UUID(guest["id"]),
            group_id=uuid.UUID(group["id"]),
            role=UserRole.GUEST,
        )
    )

    track = Track(
        added_by_user_id=uuid.UUID(owner["id"]),
        service=StreamingService.YANDEX_MUSIC,
        title="Guest Song",
        duration=200,
        external_url="https://music.yandex.ru/track/guest-song",
        audio_storage_key=None,
    )
    db_session.add(track)
    await db_session.commit()

    add_response = await client.post(
        f"/playlist/{group['id']}/{playlist_id}/tracks",
        headers=guest_headers,
        json={"internal_track_id": track.id},
    )
    assert add_response.status_code == 201, add_response.text
    assert add_response.json()["created_new_track"] is False
    assert add_response.json()["track_id"] == track.id

    duplicate_response = await client.post(
        f"/playlist/{group['id']}/{playlist_id}/tracks",
        headers=guest_headers,
        json={"internal_track_id": track.id},
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == "PLAYLIST_TRACK_ALREADY_EXISTS"


async def test_add_track_to_playlist_blocks_viewer_role(client, db_session: AsyncSession) -> None:
    owner = await register_user(client=client, email="add_track_view_owner@example.com", name="Owner")
    owner_headers = await login_user(client=client, email="add_track_view_owner@example.com")
    group = await create_group(client=client, headers=owner_headers, name="Viewer Block Group")

    create_playlist_response = await client.post(
        f"/playlist/{group['id']}/create",
        headers=owner_headers,
        json={"name": "Viewer Protected Playlist"},
    )
    assert create_playlist_response.status_code == 201, create_playlist_response.text
    playlist_id = create_playlist_response.json()["id"]

    viewer = await register_user(client=client, email="add_track_viewer@example.com", name="Viewer")
    viewer_headers = await login_user(client=client, email="add_track_viewer@example.com")
    db_session.add(
        Connection(
            user_id=uuid.UUID(viewer["id"]),
            group_id=uuid.UUID(group["id"]),
            role=UserRole.VIEWER,
        )
    )
    track = Track(
        added_by_user_id=uuid.UUID(owner["id"]),
        service=StreamingService.YANDEX_MUSIC,
        title="Viewer Song",
        duration=201,
        external_url="https://music.yandex.ru/track/viewer-song",
        audio_storage_key=None,
    )
    db_session.add(track)
    await db_session.commit()

    response = await client.post(
        f"/playlist/{group['id']}/{playlist_id}/tracks",
        headers=viewer_headers,
        json={"internal_track_id": track.id},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "GROUP_TRACK_EDIT_FORBIDDEN"
