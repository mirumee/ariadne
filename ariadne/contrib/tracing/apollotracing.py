from datetime import datetime
from inspect import isawaitable
from typing import Any, List, Optional, cast

from graphql import GraphQLResolveInfo

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


TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class ApolloTracingExtension(Extension):
    def __init__(self, trace_default_resolver: bool = False) -> None:
        self.trace_default_resolver = trace_default_resolver
        self.start_date: Optional[datetime] = None
        self.start_timestamp: int = 0
        self.resolvers: List[dict] = []

        self._totals = None

    def request_started(self, context: ContextValue):
        self.start_date = datetime.utcnow()
        self.start_timestamp = perf_counter_ns()

    async def resolve(
        self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ):
        if not should_trace(info, self.trace_default_resolver):
            result = next_(obj, info, **kwargs)
            if isawaitable(result):
                result = await result
            return result

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
            if isawaitable(result):
                result = await result
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
            "end": datetime.utcnow(),
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


class ApolloTracingExtensionSync(ApolloTracingExtension):
    def resolve(
        self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ):  # pylint: disable=invalid-overridden-method
        if not should_trace(info):
            result = next_(obj, info, **kwargs)
            return result

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
