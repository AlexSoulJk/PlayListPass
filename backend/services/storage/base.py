import re
from abc import ABC, abstractmethod

from services.storage.types import ALLOWED_FORMATS_BY_ENTITY, StorageObjectDescriptor


class StorageServiceError(RuntimeError):
    pass


class InvalidStorageFormatError(StorageServiceError):
    pass


class StorageObjectNotFoundError(StorageServiceError):
    pass


class StorageServiceBase(ABC):
    def __init__(self, *, bucket_name: str, presigned_url_ttl_seconds: int = 900) -> None:
        self.bucket_name = bucket_name
        self.presigned_url_ttl_seconds = presigned_url_ttl_seconds

    def validate_descriptor(self, descriptor: StorageObjectDescriptor) -> None:
        allowed_formats = ALLOWED_FORMATS_BY_ENTITY[descriptor.entity]
        if descriptor.file_format not in allowed_formats:
            raise InvalidStorageFormatError(
                f"Format '{descriptor.file_format.value}' is not allowed for entity '{descriptor.entity.value}'",
            )

    def normalize_filename(self, descriptor: StorageObjectDescriptor) -> str:
        default_name = f"{descriptor.entity.value}-{descriptor.entity_id}"
        source_name = descriptor.filename or default_name
        cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", source_name).strip("-.")
        return cleaned or default_name

    def build_object_key(self, descriptor: StorageObjectDescriptor) -> str:
        self.validate_descriptor(descriptor)
        safe_name = self.normalize_filename(descriptor)
        return f"{descriptor.entity.value}/{descriptor.entity_id}/{safe_name}.{descriptor.file_format.value}"

    @abstractmethod
    async def create_object(self, *, object_key: str, data: bytes, content_type: str | None = None) -> None:
        pass

    @abstractmethod
    async def read_object(self, *, object_key: str) -> bytes:
        pass

    @abstractmethod
    async def update_object(self, *, object_key: str, data: bytes, content_type: str | None = None) -> None:
        pass

    @abstractmethod
    async def delete_object(self, *, object_key: str) -> None:
        pass

    @abstractmethod
    async def object_exists(self, *, object_key: str) -> bool:
        pass

    @abstractmethod
    async def generate_presigned_upload_url(
        self,
        *,
        object_key: str,
        content_type: str | None = None,
    ) -> str:
        pass

    @abstractmethod
    async def generate_presigned_download_url(self, *, object_key: str) -> str:
        pass

    @abstractmethod
    def build_public_url(self, *, object_key: str) -> str:
        pass

    async def save_file(
        self,
        *,
        descriptor: StorageObjectDescriptor,
        data: bytes,
        content_type: str | None = None,
    ) -> str:
        object_key = self.build_object_key(descriptor)
        await self.create_object(object_key=object_key, data=data, content_type=content_type)
        return object_key

    async def remove_file(self, *, object_key: str) -> None:
        await self.delete_object(object_key=object_key)
