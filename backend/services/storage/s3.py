import asyncio
from typing import Any
from urllib.parse import urlparse, urlunparse

try:
    import boto3
    from botocore.exceptions import ClientError
except ModuleNotFoundError:
    boto3 = None
    ClientError = Exception

from services.storage.base import StorageObjectNotFoundError, StorageServiceBase


class S3StorageService(StorageServiceBase):
    def __init__(
        self,
        *,
        bucket_name: str,
        region_name: str,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        public_base_url: str | None = None,
        presigned_public_base_url: str | None = None,
        presigned_url_ttl_seconds: int = 900,
    ) -> None:
        super().__init__(
            bucket_name=bucket_name,
            presigned_url_ttl_seconds=presigned_url_ttl_seconds,
        )
        if boto3 is None:
            raise RuntimeError("BOTO3_NOT_INSTALLED")

        self.region_name = region_name
        self.endpoint_url = endpoint_url
        self.public_base_url = public_base_url
        self.presigned_public_base_url = presigned_public_base_url

        session = boto3.session.Session()
        self.client = session.client(
            "s3",
            region_name=region_name,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    @staticmethod
    def _is_not_found_error(error: Exception) -> bool:
        response = getattr(error, "response", None)
        if not isinstance(response, dict):
            return False
        code = str(response.get("Error", {}).get("Code", ""))
        return code in {"404", "NoSuchKey", "NotFound"}

    async def _run(self, func: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(func, **kwargs)

    async def create_object(self, *, object_key: str, data: bytes, content_type: str | None = None) -> None:
        put_kwargs: dict[str, Any] = {
            "Bucket": self.bucket_name,
            "Key": object_key,
            "Body": data,
        }
        if content_type:
            put_kwargs["ContentType"] = content_type

        await self._run(self.client.put_object, **put_kwargs)

    async def read_object(self, *, object_key: str) -> bytes:
        try:
            response = await self._run(
                self.client.get_object,
                Bucket=self.bucket_name,
                Key=object_key,
            )
        except ClientError as error:
            if self._is_not_found_error(error):
                raise StorageObjectNotFoundError(f"Object '{object_key}' not found") from error
            raise

        body = response["Body"]
        return await asyncio.to_thread(body.read)

    async def update_object(self, *, object_key: str, data: bytes, content_type: str | None = None) -> None:
        await self.create_object(object_key=object_key, data=data, content_type=content_type)

    async def delete_object(self, *, object_key: str) -> None:
        await self._run(
            self.client.delete_object,
            Bucket=self.bucket_name,
            Key=object_key,
        )

    async def object_exists(self, *, object_key: str) -> bool:
        try:
            await self._run(
                self.client.head_object,
                Bucket=self.bucket_name,
                Key=object_key,
            )
            return True
        except ClientError as error:
            if self._is_not_found_error(error):
                return False
            raise

    async def generate_presigned_upload_url(
        self,
        *,
        object_key: str,
        content_type: str | None = None,
    ) -> str:
        params: dict[str, Any] = {
            "Bucket": self.bucket_name,
            "Key": object_key,
        }
        if content_type:
            params["ContentType"] = content_type

        signed_url = await self._run(
            self.client.generate_presigned_url,
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=self.presigned_url_ttl_seconds,
        )
        return self._rewrite_presigned_url(signed_url)

    async def generate_presigned_download_url(self, *, object_key: str) -> str:
        signed_url = await self._run(
            self.client.generate_presigned_url,
            ClientMethod="get_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": object_key,
            },
            ExpiresIn=self.presigned_url_ttl_seconds,
        )
        return self._rewrite_presigned_url(signed_url)

    def build_public_url(self, *, object_key: str) -> str:
        if self.public_base_url:
            return f"{self.public_base_url.rstrip('/')}/{object_key}"

        if self.endpoint_url:
            return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{object_key}"

        return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{object_key}"

    def _rewrite_presigned_url(self, url: str) -> str:
        if not self.presigned_public_base_url:
            return url

        target = urlparse(self.presigned_public_base_url)
        if not target.scheme or not target.netloc:
            return url

        signed = urlparse(url)
        prefix_path = target.path.rstrip("/")
        merged_path = f"{prefix_path}{signed.path}" if prefix_path else signed.path
        return urlunparse(
            (
                target.scheme,
                target.netloc,
                merged_path,
                signed.params,
                signed.query,
                signed.fragment,
            )
        )
