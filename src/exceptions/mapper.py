from exceptions.exceptions import (
    CollectionNotFoundError,
    DataAlreadyUploadedError,
    DataHashError,
    DataUploadIncompleteError,
    FileDownloadError,
    FileUploadError,
    InvalidDataFormatError,
    InvalidVersionStateError,
    ItemConflictError,
    ItemNotFoundError,
    VersionNotFoundError,
)

STORAGE_ERROR_STATUS_MAP: dict[type[Exception], int] = {
    CollectionNotFoundError: 404,
    VersionNotFoundError: 404,
    ItemNotFoundError: 404,
    DataAlreadyUploadedError: 409,
    InvalidVersionStateError: 409,
    ItemConflictError: 409,
    DataHashError: 422,
    InvalidDataFormatError: 422,
    DataUploadIncompleteError: 422,
    FileUploadError: 502,
    FileDownloadError: 502,
}
