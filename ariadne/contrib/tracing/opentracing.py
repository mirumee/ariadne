import os
from functools import partial
from inspect import isawaitable
from typing import Any, Callable, Dict, Optional, Union

from graphql import GraphQLResolveInfo
from opentracing import Scope, Tracer, global_tracer
from opentracing.ext import tags
from starlette.datastructures import UploadFile

from ...types import ContextValue, Extension, Resolver
from .utils import format_path, should_trace

try:
    from multipart.multipart import File
except ImportError:

    class File:  # type: ignore
        """Mock upload file used when python-multipart is not installed."""


ArgFilter = Callable[[Dict[str, Any], GraphQLResolveInfo], Dict[str, Any]]


class OpenTracingExtension(Extension):
    _arg_filter: Optional[ArgFilter]
    _root_scope: Scope
    _tracer: Tracer

    def __init__(self, *, arg_filter: Optional[ArgFilter] = None) -> None:
        self._arg_filter = arg_filter
        self._tracer = global_tracer()

    def request_started(self, context: ContextValue):
        self._root_scope = self._tracer.start_active_span("GraphQL Query")
        self._root_scope.span.set_tag(tags.COMPONENT, "graphql")

    def request_finished(self, context: ContextValue):
        self._root_scope.close()

    async def resolve(
        self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ):
        if not should_trace(info):
            result = next_(obj, info, **kwargs)
            if isawaitable(result):
                result = await result
            return result

        with self._tracer.start_active_span(info.field_name) as scope:
            span = scope.span
            span.set_tag(tags.COMPONENT, "graphql")
            span.set_tag("graphql.parentType", info.parent_type.name)

            graphql_path = ".".join(
                map(str, format_path(info.path))  # pylint: disable=bad-builtin
            )
            span.set_tag("graphql.path", graphql_path)

            if kwargs:
                filtered_kwargs = self.filter_resolver_args(kwargs, info)
                for kwarg, value in filtered_kwargs.items():
                    span.set_tag(f"graphql.param.{kwarg}", value)

            result = next_(obj, info, **kwargs)
            if isawaitable(result):
                result = await result
            return result

    def filter_resolver_args(
        self, args: Dict[str, Any], info: GraphQLResolveInfo
    ) -> Dict[str, Any]:
        args_to_trace = copy_args_for_tracing(args)

        if not self._arg_filter:
            return args_to_trace

        return self._arg_filter(args_to_trace, info)


class OpenTracingExtensionSync(OpenTracingExtension):
    def resolve(
        self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ):  # pylint: disable=invalid-overridden-method
        if not should_trace(info):
            result = next_(obj, info, **kwargs)
            return result

        with self._tracer.start_active_span(info.field_name) as scope:
            span = scope.span
            span.set_tag(tags.COMPONENT, "graphql")
            span.set_tag("graphql.parentType", info.parent_type.name)

            graphql_path = ".".join(
                map(str, format_path(info.path))  # pylint: disable=bad-builtin
            )
            span.set_tag("graphql.path", graphql_path)

            if kwargs:
                filtered_kwargs = self.filter_resolver_args(kwargs, info)
                for kwarg, value in filtered_kwargs.items():
                    span.set_tag(f"graphql.param.{kwarg}", value)

            result = next_(obj, info, **kwargs)
            return result


def opentracing_extension(*, arg_filter: Optional[ArgFilter] = None):
    return partial(OpenTracingExtension, arg_filter=arg_filter)


def opentracing_extension_sync(*, arg_filter: Optional[ArgFilter] = None):
    return partial(OpenTracingExtensionSync, arg_filter=arg_filter)


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
