import datetime
import time
from inspect import isawaitable

from graphql import GraphQLResolveInfo, ResponsePath


def format_path(path: ResponsePath):
    elements = []
    while path:
        elements.append(path.key)
        path = path.prev
    return elements[::-1]


class TracingMiddleware:
    def __init__(self):
        self.start_date = datetime.datetime.utcnow()
        self.start_timestamp = time.perf_counter_ns()
        self.parsing_start_timestamp = self.start_timestamp
        self.parsing_end_timestamp = self.start_timestamp
        self.validation_start_timestamp = self.start_timestamp
        self.validation_end_timestamp = self.start_timestamp
        self.resolvers = []

    def start_validation(self):
        self.validation_start_timestamp = time.perf_counter_ns()

    def end_validation(self):
        self.validation_end_timestamp = time.perf_counter_ns()

    def should_trace(self, info: GraphQLResolveInfo):
        path = info.path
        while path:
            if isinstance(path.key, str) and path.key.startswith('__'):
                return False
            path = path.prev
        if info.parent_type.fields[info.field_name].resolve is None:
            return False
        return True

    async def resolve(self, next_, parent, info: GraphQLResolveInfo, **kwargs):
        if not self.should_trace(info):
            return next_(parent, info, **kwargs)

        start_timestamp = time.perf_counter_ns()
        record = {
            "path": format_path(info.path),
            "parentType": str(info.parent_type),
            "fieldName": info.field_name,
            "returnType": str(info.return_type),
            "startOffset": start_timestamp - self.start_timestamp,
        }
        self.resolvers.append(record)
        try:
            result = next_(parent, info, **kwargs)
            if isawaitable(result):
                result = await result
            return result
        finally:
            end_timestamp = time.perf_counter_ns()
            record["duration"] = end_timestamp - start_timestamp

    def extension_data(self):
        return {
            "tracing": {
                "version": 1,
                "startTime": self.start_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "endTime": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "duration": time.perf_counter_ns() - self.start_timestamp,
                "parsing": {
                    "startOffset": self.parsing_start_timestamp - self.start_timestamp,
                    "duration": self.parsing_end_timestamp
                    - self.parsing_start_timestamp,
                },
                "validation": {
                    "startOffset": self.validation_start_timestamp
                    - self.start_timestamp,
                    "duration": self.validation_end_timestamp
                    - self.validation_start_timestamp,
                },
                "execution": {"resolvers": self.resolvers},
            }
        }
