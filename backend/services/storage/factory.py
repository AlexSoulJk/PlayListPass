from functools import lru_cache

from services.settings import settings
from services.storage.s3 import S3StorageService


@lru_cache
def get_s3_storage_service() -> S3StorageService:
    return S3StorageService(
        bucket_name=settings.S3_BUCKET_NAME,
        region_name=settings.S3_REGION_NAME,
        endpoint_url=settings.S3_ENDPOINT_URL,
        access_key_id=settings.S3_ACCESS_KEY_ID,
        secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        public_base_url=settings.S3_PUBLIC_BASE_URL,
        presigned_public_base_url=settings.S3_PRESIGNED_PUBLIC_BASE_URL,
        presigned_url_ttl_seconds=settings.S3_PRESIGNED_URL_TTL_SECONDS,
    )
