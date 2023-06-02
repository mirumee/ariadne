import os
from functools import partial
from inspect import iscoroutinefunction
from typing import Any, Callable, Dict, Optional, Union

from graphql import GraphQLResolveInfo
from graphql.pyutils import is_awaitable
from opentracing import Scope, Span, Tracer, global_tracer
from opentracing.ext import tags
from starlette.datastructures import UploadFile

from ...types import ContextValue, Extension, Resolver
from .utils import format_path, should_trace

try:
    from multipart.multipart import File
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
    if isinstance(upload_file, File):
        filename = upload_file.file_name
    else:
        filename = upload_file.filename

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
