import os
from typing import Any, Union

from starlette.datastructures import UploadFile

try:
    from python_multipart.multipart import File
except ImportError:

    class File:  # type: ignore
        """Mock upload file used when python-multipart is not installed."""


def copy_args_for_tracing(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: copy_args_for_tracing(v) for k, v in value.items()}
    if isinstance(value, list):
        return [copy_args_for_tracing(v) for v in value]
    if isinstance(value, (UploadFile, File)):
        return repr_upload_file(value)
    return value


def repr_upload_file(upload_file: Union[UploadFile, File]) -> str:
    filename: Union[str, None, bytes]
    if isinstance(upload_file, File):
        filename = upload_file.file_name
    else:
        filename = upload_file.filename

    if isinstance(filename, bytes):
        filename = filename.decode()

    mime_type: Union[str, None]

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
