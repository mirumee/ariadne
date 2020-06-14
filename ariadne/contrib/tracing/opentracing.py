from copy import deepcopy
from functools import partial
from inspect import isawaitable
from typing import Any, Callable, Dict, Optional

from graphql import GraphQLResolveInfo
from opentracing import Scope, Tracer, global_tracer
from opentracing.ext import tags

from ...types import ContextValue, Extension, Resolver
from .utils import format_path, should_trace

ArgFilter = Callable[[Dict[str, Any], GraphQLResolveInfo], Dict[str, Any]]


class OpenTracingExtension(Extension):
    _arg_filter: Optional[ArgFilter]
    _root_scope: Scope
    _tracer: Tracer

    def __init__(self, *, arg_filter: Optional[ArgFilter] = None):
        self._arg_filter = arg_filter
        self._tracer = global_tracer()
        self._root_scope = None

    def request_started(self, context: ContextValue):
        self._root_scope = self._tracer.start_active_span("GraphQL Query")
        self._root_scope.span.set_tag(tags.COMPONENT, "graphql")

    def request_finished(self, context: ContextValue):
        self._root_scope.close()

    async def resolve(
        self, next_: Resolver, parent: Any, info: GraphQLResolveInfo, **kwargs
    ):
        if not should_trace(info):
            result = next_(parent, info, **kwargs)
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

            result = next_(parent, info, **kwargs)
            if isawaitable(result):
                result = await result
            return result

    def filter_resolver_args(
        self, args: Dict[str, Any], info: GraphQLResolveInfo
    ) -> Dict[str, Any]:
        if not self._arg_filter:
            return args

        return self._arg_filter(deepcopy(args), info)


class OpenTracingExtensionSync(OpenTracingExtension):
    def resolve(
        self, next_: Resolver, parent: Any, info: GraphQLResolveInfo, **kwargs
    ):  # pylint: disable=invalid-overridden-method
        if not should_trace(info):
            result = next_(parent, info, **kwargs)
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

            result = next_(parent, info, **kwargs)
            return result


def opentracing_extension(*, arg_filter: Optional[ArgFilter] = None):
    return partial(OpenTracingExtension, arg_filter=arg_filter)


def opentracing_extension_sync(*, arg_filter: Optional[ArgFilter] = None):
    return partial(OpenTracingExtensionSync, arg_filter=arg_filter)
