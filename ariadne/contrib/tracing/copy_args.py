import os
from typing import Any

from starlette.datastructures import UploadFile

try:
    from python_multipart.multipart import File  # type: ignore[import-untyped]
except ImportError:

    class File:
        """Mock upload file used when python-multipart is not installed."""

        file_name: bytes | None = None
        size: int = 0


def copy_args_for_tracing(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: copy_args_for_tracing(v) for k, v in value.items()}
    if isinstance(value, list):
        return [copy_args_for_tracing(v) for v in value]
    if isinstance(value, UploadFile | File):
        return repr_upload_file(value)
    return value


def repr_upload_file(upload_file: UploadFile | File) -> str:
    filename: str | None | bytes
    if isinstance(upload_file, File):
        filename = upload_file.file_name
    else:
        filename = upload_file.filename

    if isinstance(filename, bytes):
        filename = filename.decode()

    mime_type: str | None

    if isinstance(upload_file, File):
        mime_type = "not/available"
    else:
        mime_type = upload_file.content_type

    if isinstance(upload_file, File):
        size = upload_file.size
    else:
        file_ = upload_file.file
        file_.seek(0, os.SEEK_END)
        size = file_.tell()
        file_.seek(0)

    return (
        f"{type(upload_file)}(mime_type={mime_type}, size={size}, filename={filename})"
    )
