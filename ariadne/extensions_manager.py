from typing import List

from graphql.execution import MiddlewareManager

from .types import Extension


class ExtensionsManager:
    def __init__(self, extensions: List[Extension]):
        self.extensions = tuple(ext() for ext in extensions) if extensions else tuple()

    def as_middleware_manager(self):
        return MiddlewareManager(*self.extensions)

    def parsing_did_start(self, query):
        for extension in self.extensions:
            extension.parsing_did_start(query)

    def parsing_did_end(self):
        for extension in reversed(self.extensions):
            extension.parsing_did_end()

    def validation_did_start(self):
        for extension in self.extensions:
            extension.validation_did_start()

    def validation_did_end(self):
        for extension in reversed(self.extensions):
            extension.validation_did_end()
    
    def execution_did_start(self):
        for extension in self.extensions:
            extension.execution_did_start()

    def execution_did_end(self):
        for extension in reversed(self.extensions):
            extension.execution_did_end()

    def will_send_response(self, result, context=None):
        if callable(context):
            context = None

        _, data = result
        if not "extensions" in data:
            data["extensions"] = {}
        for extension in reversed(self.extensions):
            result = extension.will_send_response(result, context)
        return result