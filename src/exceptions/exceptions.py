import uuid
from typing import Any, List, Optional

from error_handler.base_exception import BaseError


class StorageError(BaseError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        self.message = message
        self.extra = kwargs
        super().__init__(self.message, **kwargs)


class CollectionNotFoundError(StorageError):
    def __init__(
        self,
        collection_uuid: uuid.UUID,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        kwargs["collection_uuid"] = str(collection_uuid)
        default_message = f"Collection with UUID '{collection_uuid}' was not found."
        super().__init__(message or default_message, **kwargs)


class VersionNotFoundError(StorageError):
    def __init__(
        self,
        collection_uuid: uuid.UUID,
        version_uuid: uuid.UUID,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        kwargs["collection_uuid"] = str(collection_uuid)
        kwargs["version_uuid"] = str(version_uuid)
        default_message = (
            f"Version with UUID '{version_uuid}' belonging to collection "
            f"'{collection_uuid}' was not found."
        )
        super().__init__(message or default_message, **kwargs)


class ItemNotFoundError(StorageError):
    def __init__(
        self,
        collection_uuid: uuid.UUID,
        version_uuid: uuid.UUID,
        item_uuid: uuid.UUID,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        kwargs["collection_uuid"] = str(collection_uuid)
        kwargs["version_uuid"] = str(version_uuid)
        kwargs["item_uuid"] = str(item_uuid)
        default_message = f"Item with UUID '{item_uuid}' was not found."
        super().__init__(message or default_message, **kwargs)


class InvalidVersionStateError(StorageError):
    def __init__(
        self,
        collection_uuid: uuid.UUID,
        version_uuid: uuid.UUID,
        current_version_state: str,
        action: str,
        required_state: List[str],
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        kwargs["collection_uuid"] = str(collection_uuid)
        kwargs["version_uuid"] = str(version_uuid)
        kwargs["current_version_state"] = current_version_state
        kwargs["action"] = action
        kwargs["required_state"] = required_state
        states_string = ", ".join(f"'{state}'" for state in required_state)
        default_message = (
            f"Version '{version_uuid}' is in state '{current_version_state}'. "
            f"Action '{action}' requires: {states_string}."
        )
        super().__init__(message or default_message, **kwargs)


class DataAlreadyUploadedError(StorageError):
    def __init__(
        self,
        item_uuid: uuid.UUID,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        kwargs["item_uuid"] = str(item_uuid)
        default_message = f"Data for item '{item_uuid}' has already been uploaded."
        super().__init__(message or default_message, **kwargs)


class DataHashError(StorageError):
    def __init__(
        self,
        expected_hash: str,
        actual_hash: str,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        kwargs["expected_hash"] = expected_hash
        kwargs["actual_hash"] = actual_hash
        default_message = (
            f"Data hash mismatch. Expected '{expected_hash}', got '{actual_hash}'."
        )
        super().__init__(message or default_message, **kwargs)


class InvalidDataFormatError(StorageError):
    def __init__(
        self,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        default_message = "Data must contain valid base64."
        super().__init__(message or default_message, **kwargs)


class DataUploadIncompleteError(StorageError):
    def __init__(
        self,
        collection_uuid: uuid.UUID,
        version_uuid: uuid.UUID,
        missing_items: List[uuid.UUID],
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        kwargs["collection_uuid"] = str(collection_uuid)
        kwargs["version_uuid"] = str(version_uuid)
        kwargs["missing_items"] = [str(item_uuid) for item_uuid in missing_items]
        default_message = "Not all item data has been uploaded."
        super().__init__(message or default_message, **kwargs)


class ItemConflictError(StorageError):
    def __init__(
        self,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        default_message = "Item UUIDs and paths must be unique inside a version."
        super().__init__(message or default_message, **kwargs)


class FileUploadError(StorageError):
    def __init__(
        self,
        link: str,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        kwargs["link"] = link
        default_message = "Failed to upload item data to object storage."
        super().__init__(message or default_message, **kwargs)


class FileDownloadError(StorageError):
    def __init__(
        self,
        link: str,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        kwargs["link"] = link
        default_message = "Failed to download item data from object storage."
        super().__init__(message or default_message, **kwargs)
