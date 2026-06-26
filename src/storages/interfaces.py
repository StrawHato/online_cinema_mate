from abc import ABC, abstractmethod


class StorageInterface(ABC):

    @abstractmethod
    async def upload_file(
        self,
        file_name: str,
        file_data: bytes,
        content_type: str,
    ) -> None:
        """
        Upload a file to object storage.
        """
        ...

    @abstractmethod
    async def get_file_url(
        self,
        file_name: str,
    ) -> str:
        """
        Return public URL for a stored file.
        """
        ...
