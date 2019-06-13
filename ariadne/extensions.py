from contextlib import contextmanager
from inspect import isawaitable
from typing import List

from graphql.execution import MiddlewareManager

from .types import Extension


class ExtensionManager:
    __slots__ = ("extensions", "extensions_reversed")

    def __init__(self, extensions: List[Extension]):
        self.extensions = tuple(ext() for ext in extensions) if extensions else tuple()
        self.extensions_reversed = tuple(reversed(self.extensions))

    def as_middleware_manager(self, middleware):
        if middleware and middleware.middlewares:
            return MiddlewareManager(*self.extensions, *middleware.middlewares)
        return MiddlewareManager(*self.extensions)

    @contextmanager
    def request(self, context):
        for ext in self.extensions:
            ext.request_started(context)
        try:
            yield
        except Exception as e:
            for ext in self.extensions_reversed:
                ext.request_finished(context, e)
            raise
        else:
            for ext in self.extensions_reversed:
                ext.request_finished(context)

    @contextmanager
    def parsing(self, query):
        for ext in self.extensions:
            ext.parsing_started(query)
        try:
            yield
        except Exception as e:
            for ext in self.extensions_reversed:
                ext.parsing_finished(query, e)
            raise
        else:
            for ext in self.extensions_reversed:
                ext.parsing_finished(query)

    @contextmanager
    def validation(self, context):
        for ext in self.extensions:
            ext.validation_started(context)
        try:
            yield
        except Exception as e:
            for ext in self.extensions_reversed:
                ext.validation_finished(context, e)
            raise
        else:
            for ext in self.extensions_reversed:
                ext.validation_finished(context)

    @contextmanager
    def execution(self, context):
        for ext in self.extensions:
            ext.execution_started(context)
        try:
            yield
        except Exception as e:
            for ext in self.extensions_reversed:
                ext.execution_finished(context, e)
            raise
        else:
            for ext in self.extensions_reversed:
                ext.execution_finished(context)

    def has_errors(self, errors):
        for ext in self.extensions:
            ext.has_errors(errors)

    def format(self):
        data = {}
        for ext in self.extensions:
            ext_data = ext.format()
            if ext_data:
                data.update(ext_data)
        return data
