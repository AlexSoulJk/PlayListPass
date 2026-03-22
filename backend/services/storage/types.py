import uuid
from dataclasses import dataclass
from enum import StrEnum


class StorageEntity(StrEnum):
    GROUP = "groups"
    PLAYLIST = "playlists"
    TRACK = "tracks"


class StorageFileFormat(StrEnum):
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    MP3 = "mp3"


ALLOWED_FORMATS_BY_ENTITY: dict[StorageEntity, set[StorageFileFormat]] = {
    StorageEntity.GROUP: {
        StorageFileFormat.JPG,
        StorageFileFormat.JPEG,
        StorageFileFormat.PNG,
        StorageFileFormat.WEBP,
    },
    StorageEntity.PLAYLIST: {
        StorageFileFormat.JPG,
        StorageFileFormat.JPEG,
        StorageFileFormat.PNG,
        StorageFileFormat.WEBP,
    },
    StorageEntity.TRACK: {
        StorageFileFormat.JPG,
        StorageFileFormat.JPEG,
        StorageFileFormat.PNG,
        StorageFileFormat.WEBP,
        StorageFileFormat.MP3,
    },
}


@dataclass(frozen=True, slots=True)
class StorageObjectDescriptor:
    entity: StorageEntity
    file_format: StorageFileFormat
    entity_id: uuid.UUID
    filename: str | None = None
