import aioboto3
from botocore.exceptions import (
    BotoCoreError,
    ConnectionError,
    HTTPClientError,
    NoCredentialsError,
)

from src.exceptions import (
    S3ConnectionError,
    S3FileUploadError,
)
from src.storages.interfaces import StorageInterface


class S3Storage(StorageInterface):
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
    ):
        self._endpoint_url = endpoint_url
        self._bucket_name = bucket_name

        self._session = aioboto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    async def upload_file(
        self,
        file_name: str,
        file_data: bytes,
        content_type: str,
    ) -> None:
        try:
            async with self._session.client(
                "s3",
                endpoint_url=self._endpoint_url,
            ) as client:
                await client.put_object(
                    Bucket=self._bucket_name,
                    Key=file_name,
                    Body=file_data,
                    ContentType=content_type,
                )

        except (
            ConnectionError,
            HTTPClientError,
            NoCredentialsError,
        ) as error:
            raise S3ConnectionError(
                f"Failed to connect to S3 storage: {error}"
            ) from error

        except BotoCoreError as error:
            raise S3FileUploadError(
                f"Failed to upload file: {error}"
            ) from error

    async def get_file_url(
        self,
        file_name: str,
    ) -> str:
        return (
            f"{self._endpoint_url}/"
            f"{self._bucket_name}/"
            f"{file_name}"
        )
