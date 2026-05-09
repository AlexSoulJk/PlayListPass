from database.models.models import Group, Playlist, User
from database.repos.playlist_repos import PlaylistRepos
from schemas.playlist import PlaylistCreateRequest, PlaylistItemResponse
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status


class PlayListManager:
    def __init__(self, playlist_repository: PlaylistRepos) -> None:
        self.playlist_repository = playlist_repository

    async def create_playlist(
        self,
        *,
        user: User,
        payload: PlaylistCreateRequest,
        group: Group,
    ) -> PlaylistItemResponse:
        _ = user  # Reserved for future permission/business logic.
        try:
            playlist = await self.playlist_repository.create_playlist(
                playlist_name=payload.name,
                group_id=group.id,
                image_url=payload.image_url,
            )
        except IntegrityError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PLAYLIST_NAME_ALREADY_EXISTS",
            ) from error

        return PlaylistItemResponse(
            id=playlist.id,
            name=playlist.name,
            image_url=playlist.image_url,
        )

    async def delete_playlist(self, *, user: User, playlist: Playlist):
        _ = user
        _ = playlist

    async def remove_song_from_playlist(self, playlist_id, song_id):
        _ = playlist_id
        _ = song_id

    async def get_user_playlists(self, user_id):
        _ = user_id
