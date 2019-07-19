import datetime
import time

import opentracing

from ...types import ContextValue, Extension, Resolver


class OpenTracingExtension(Extension):
    def request_started(self, *_):
        self._query_span = opentracing.global_tracer().start_span("GraphQL Query")

    def request_finished(self, *_):
        self._query_span.finish()

    async def resolve(
        self, next_: Resolver, parent: Any, info: GraphQLResolveInfo, **kwargs
    ):
        if not should_trace(info):
            return next_(parent, info, **kwargs)

        with opentracing.global_tracer().start_span(info.field_name) as span:
            result = next_(parent, info, **kwargs)
            if isawaitable(result):
                result = await result
            return result