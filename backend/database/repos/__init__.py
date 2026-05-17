from __future__ import annotations

from importlib import import_module

__all__ = [
    "ArtistRepos",
    "ArtistServiceLinkRepos",
    "GroupRepos",
    "PlaylistRepos",
    "TrackArtistRepos",
    "TrackServiceLinkRepos",
    "TrackRepos",
    "YandexTrackRepos",
]

_EXPORT_TO_MODULE = {
    "ArtistRepos": "database.repos.artist_repos",
    "ArtistServiceLinkRepos": "database.repos.artist_service_link_repos",
    "GroupRepos": "database.repos.group_repos",
    "PlaylistRepos": "database.repos.playlist_repos",
    "TrackArtistRepos": "database.repos.track_artist_repos",
    "TrackServiceLinkRepos": "database.repos.track_service_link_repos",
    "TrackRepos": "database.repos.track_repos",
    "YandexTrackRepos": "database.repos.yandex_track_repos",
}


def __getattr__(name: str):
    module_path = _EXPORT_TO_MODULE.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_path)
    return getattr(module, name)
