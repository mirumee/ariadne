from functools import partial
from inspect import iscoroutinefunction
from typing import Any, Callable, Optional, Union

from graphql import GraphQLResolveInfo
from graphql.pyutils import is_awaitable
from opentelemetry.trace import Context, Span, Tracer, get_tracer, set_span_in_context

from ...types import ContextValue, Extension, Resolver
from .utils import copy_args_for_tracing, format_path, should_trace

ArgFilter = Callable[[dict[str, Any], GraphQLResolveInfo], dict[str, Any]]
RootSpanName = Union[str, Callable[[ContextValue], str]]

DEFAULT_OPERATION_NAME = "GraphQL Operation"


class OpenTelemetryExtension(Extension):
    _arg_filter: Optional[ArgFilter]
    _root_context: Optional[Context]
    _root_span: Span
    _root_span_name: Optional[RootSpanName]
    _tracer: Tracer

    def __init__(
        self,
        *,
        tracer: Optional[Tracer] = None,
        arg_filter: Optional[ArgFilter] = None,
        root_context: Optional[Context] = None,
        root_span_name: Optional[RootSpanName] = None,
    ) -> None:
        if tracer:
            self._tracer = tracer
        else:
            self._tracer = get_tracer("ariadne")

        self._arg_filter = arg_filter
        self._root_context = root_context
        self._root_span_name = root_span_name

    def request_started(self, context: ContextValue):
        if self._root_span_name:
            if callable(self._root_span_name):
                root_span_name = self._root_span_name(context)
            else:
                root_span_name = self._root_span_name
        else:
            root_span_name = DEFAULT_OPERATION_NAME

        span_context: Optional[Context] = None
        if self._root_context:
            span_context = self._root_context

        root_span = self._tracer.start_span(root_span_name, context=span_context)
        root_span.set_attribute("component", "GraphQL")
        self._root_span = root_span

    def request_finished(self, context: ContextValue):
        self._root_span.end()

    def resolve(
        self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ) -> Any:
        if not should_trace(info):
            return next_(obj, info, **kwargs)

        graphql_path = ".".join(map(str, format_path(info.path)))

        with self._tracer.start_as_current_span(
            info.field_name, context=set_span_in_context(self._root_span)
        ) as span:
            span.set_attribute("component", "GraphQL")

            if info.operation.name:
                span.set_attribute("graphql.operation.name", info.operation.name.value)
            else:
                span.set_attribute("graphql.operation.name", DEFAULT_OPERATION_NAME)

            span.set_attribute("graphql.parentType", info.parent_type.name)
            span.set_attribute("graphql.path", graphql_path)

            if kwargs:
                filtered_kwargs = self.filter_resolver_args(kwargs, info)
                for key, value in filtered_kwargs.items():
                    span.set_attribute(f"graphql.arg[{key}]", value)

            if iscoroutinefunction(next_):
                return self.resolve_async(span, next_, obj, info, **kwargs)

            return self.resolve_sync(span, next_, obj, info, **kwargs)

    async def resolve_async(
        self, span: Span, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ) -> Any:
        with self._tracer.start_as_current_span(
            "resolve async", context=set_span_in_context(span)
        ) as child_span:
            result = next_(obj, info, **kwargs)
            if is_awaitable(result):
                with self._tracer.start_as_current_span(
                    "await result", context=set_span_in_context(child_span)
                ):
                    return await result
            return result

    def resolve_sync(
        self, span: Span, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ) -> Any:
        with self._tracer.start_as_current_span(
            "resolve sync", context=set_span_in_context(span)
        ) as child_span:
            result = next_(obj, info, **kwargs)

            if is_awaitable(result):

                async def await_sync_result():
                    with self._tracer.start_as_current_span(
                        "await result", context=set_span_in_context(child_span)
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


def opentelemetry_extension(
    *,
    tracer: Optional[Tracer] = None,
    arg_filter: Optional[ArgFilter] = None,
    root_context: Optional[Context] = None,
    root_span_name: Optional[RootSpanName] = None,
):
    return partial(
        OpenTelemetryExtension,
        tracer=tracer,
        arg_filter=arg_filter,
        root_context=root_context,
        root_span_name=root_span_name,
    )
