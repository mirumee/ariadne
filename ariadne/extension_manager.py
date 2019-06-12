from contextlib import contextmanager
from functools import partial, reduce
from typing import List

from graphql.execution import MiddlewareManager

from .types import Extension


class ExtensionManager:
    def __init__(self, extensions: List[Extension]):
        self.extensions = tuple(ext() for ext in extensions) if extensions else tuple()
        self.extensions_reversed = tuple(reversed(self.extensions))

    def as_middleware_manager(self):
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
        formatted_extensions = {}
        for ext in self.extensions:
            formatted_extension = ext.format()
            if formatted_extension:
                formatted_extensions.update(formatted_extensions)
        return formatted_extensions
