from fastapi import HTTPException, status

from services.storage.factory import get_s3_storage_service
from services.storage.s3 import S3StorageService


async def get_storage_service() -> S3StorageService:
    try:
        return get_s3_storage_service()
    except RuntimeError as error:
        if str(error) == "BOTO3_NOT_INSTALLED":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="STORAGE_BACKEND_NOT_AVAILABLE",
            ) from error
        raise
