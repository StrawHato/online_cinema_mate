from src.storages.interfaces import StorageInterface


class FakeS3Storage(StorageInterface):
    async def upload_file(
        self,
        file_name: str,
        file_data: bytes,
        content_type: str,
    ) -> None:
        return None

    async def get_file_url(
        self,
        file_name: str,
    ) -> str:
        return f"https://fake-storage.local/{file_name}"
