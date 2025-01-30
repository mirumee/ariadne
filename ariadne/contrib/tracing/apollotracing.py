from inspect import iscoroutinefunction
from typing import Any, Optional, cast

from graphql import GraphQLResolveInfo
from graphql.pyutils import is_awaitable

from ...types import ContextValue, Extension, Resolver
from .utils import format_path, should_trace

try:
    from time import perf_counter_ns
except ImportError:
    # Py 3.6 fallback
    from time import perf_counter

    NS_IN_SECOND = 1000000000

    def perf_counter_ns() -> int:
        return int(perf_counter() * NS_IN_SECOND)


try:
    from datetime import UTC, datetime  # type: ignore[attr-defined]

    def utc_now():
        return datetime.now(UTC)

except ImportError:
    from datetime import datetime

    def utc_now():
        return datetime.utcnow()


TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class ApolloTracingExtension(Extension):
    def __init__(self, trace_default_resolver: bool = False) -> None:
        self.trace_default_resolver = trace_default_resolver
        self.start_date: Optional[datetime] = None
        self.start_timestamp: int = 0
        self.resolvers: list[dict] = []

        self._totals = None

    def request_started(self, context: ContextValue):
        self.start_date = utc_now()
        self.start_timestamp = perf_counter_ns()

    def resolve(self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs):
        if not should_trace(info, self.trace_default_resolver):
            return next_(obj, info, **kwargs)

        if iscoroutinefunction(next_):
            return self.resolve_async(next_, obj, info, **kwargs)

        return self.resolve_sync(next_, obj, info, **kwargs)

    async def resolve_async(
        self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ):
        start_timestamp = perf_counter_ns()
        record = {
            "path": format_path(info.path),
            "parentType": str(info.parent_type),
            "fieldName": info.field_name,
            "returnType": str(info.return_type),
            "startOffset": start_timestamp - cast(int, self.start_timestamp),
        }
        self.resolvers.append(record)
        try:
            result = next_(obj, info, **kwargs)
            if is_awaitable(result):
                result = await result
            return result
        finally:
            end_timestamp = perf_counter_ns()
            record["duration"] = end_timestamp - start_timestamp

    def resolve_sync(
        self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ):
        start_timestamp = perf_counter_ns()
        record = {
            "path": format_path(info.path),
            "parentType": str(info.parent_type),
            "fieldName": info.field_name,
            "returnType": str(info.return_type),
            "startOffset": start_timestamp - cast(int, self.start_timestamp),
        }
        self.resolvers.append(record)
        try:
            result = next_(obj, info, **kwargs)
            return result
        finally:
            end_timestamp = perf_counter_ns()
            record["duration"] = end_timestamp - start_timestamp

    def get_totals(self):
        if self._totals is None:
            self._totals = self._get_totals()
        return self._totals

    def _get_totals(self):
        return {
            "start": self.start_date,
            "end": utc_now(),
            "duration": perf_counter_ns() - self.start_timestamp,
            "resolvers": self.resolvers,
        }

    def format(self, context: ContextValue):
        totals = self.get_totals()

        return {
            "tracing": {
                "version": 1,
                "startTime": totals["start"].strftime(TIMESTAMP_FORMAT),
                "endTime": totals["end"].strftime(TIMESTAMP_FORMAT),
                "duration": totals["duration"],
                "execution": {"resolvers": totals["resolvers"]},
            }
        }
