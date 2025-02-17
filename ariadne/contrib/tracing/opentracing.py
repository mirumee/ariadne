from functools import partial
from inspect import iscoroutinefunction
from typing import Any, Callable, Optional, Union

from graphql import GraphQLResolveInfo
from graphql.pyutils import is_awaitable
from opentracing import Scope, Span, Tracer, global_tracer
from opentracing.ext import tags

from ...types import ContextValue, Extension, Resolver
from .utils import copy_args_for_tracing, format_path, should_trace

ArgFilter = Callable[[dict[str, Any], GraphQLResolveInfo], dict[str, Any]]
RootSpanName = Union[str, Callable[[ContextValue], str]]


class OpenTracingExtension(Extension):
    _arg_filter: Optional[ArgFilter]
    _root_scope: Scope
    _root_span_name: Optional[RootSpanName]
    _tracer: Tracer

    def __init__(
        self,
        *,
        arg_filter: Optional[ArgFilter] = None,
        root_span_name: Optional[RootSpanName] = None,
    ) -> None:
        self._arg_filter = arg_filter
        self._root_span_name = root_span_name
        self._tracer = global_tracer()

    def request_started(self, context: ContextValue):
        if self._root_span_name:
            if callable(self._root_span_name):
                root_span_name = self._root_span_name(context)
            else:
                root_span_name = self._root_span_name
        else:
            root_span_name = "GraphQL Operation"

        self._root_scope = self._tracer.start_active_span(root_span_name)
        self._root_scope.span.set_tag(tags.COMPONENT, "GraphQL")

    def request_finished(self, context: ContextValue):
        self._root_scope.close()

    def resolve(
        self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ) -> Any:
        if not should_trace(info):
            return next_(obj, info, **kwargs)

        graphql_path = ".".join(map(str, format_path(info.path)))

        with self._tracer.start_active_span(info.field_name) as scope:
            span = scope.span
            span.set_tag(tags.COMPONENT, "GraphQL")

            if info.operation.name:
                span.set_tag("graphql.operation.name", info.operation.name.value)
            else:
                span.set_tag("graphql.operation.name", "GraphQL Operation")

            span.set_tag("graphql.parentType", info.parent_type.name)
            span.set_tag("graphql.path", graphql_path)

            if kwargs:
                filtered_kwargs = self.filter_resolver_args(kwargs, info)
                for key, value in filtered_kwargs.items():
                    span.set_tag(f"graphql.arg[{key}]", value)

            if iscoroutinefunction(next_):
                return self.resolve_async(span, next_, obj, info, **kwargs)

            return self.resolve_sync(span, next_, obj, info, **kwargs)

    async def resolve_async(
        self, span: Span, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ) -> Any:
        with self._tracer.start_active_span("resolve async", child_of=span):
            result = next_(obj, info, **kwargs)
            if is_awaitable(result):
                with self._tracer.start_active_span("await result"):
                    return await result
            return result

    def resolve_sync(
        self, span: Span, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ) -> Any:
        with self._tracer.start_active_span("resolve sync", child_of=span) as scope:
            result = next_(obj, info, **kwargs)

            if is_awaitable(result):

                async def await_sync_result():
                    with self._tracer.start_active_span(
                        "await result", child_of=scope.span
                    ):
                        return await result

                return await_sync_result()

            return result

    def filter_resolver_args(
        self, args: dict[str, Any], info: GraphQLResolveInfo
    ) -> dict[str, Any]:
        args_to_trace = copy_args_for_tracing(args)

        if not self._arg_filter:
            return args_to_trace

        return self._arg_filter(args_to_trace, info)


def opentracing_extension(
    *,
    arg_filter: Optional[ArgFilter] = None,
    root_span_name: Optional[RootSpanName] = None,
):
    return partial(
        OpenTracingExtension,
        arg_filter=arg_filter,
        root_span_name=root_span_name,
    )
