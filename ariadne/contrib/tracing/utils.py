import os
from typing import Any, Union

from graphql import GraphQLResolveInfo, ResponsePath
from starlette.datastructures import UploadFile

from ...resolvers import is_default_resolver

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


def format_path(path: ResponsePath):
    elements = []
    while path:
        elements.append(path.key)
        path = path.prev
    return elements[::-1]


def should_trace(info: GraphQLResolveInfo, trace_default_resolver: bool = False):
    if info.field_name not in info.parent_type.fields:
        return False

    resolver = info.parent_type.fields[info.field_name].resolve
    if trace_default_resolver:
        default_resolver_bool = False
    else:
        default_resolver_bool = is_default_resolver(resolver)
    return not (default_resolver_bool or is_introspection_field(info))


def is_introspection_field(info: GraphQLResolveInfo):
    path = info.path
    while path:
        if isinstance(path.key, str) and is_introspection_key(path.key):
            return True
        path = path.prev
    return False


def is_introspection_key(key: str):
    return key.lower() in [
        "__schema",
        "__directive",
        "__directivelocation",
        "__type",
        "__field",
        "__inputvalue",
        "__enumvalue",
        "__typekind",
    ]  # from graphql.type.introspection.introspection_types
