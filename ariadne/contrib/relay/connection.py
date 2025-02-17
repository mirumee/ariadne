from collections.abc import Sequence
from typing import Any

from ariadne.contrib.relay.arguments import ConnectionArgumentsUnion


class RelayConnection:
    def __init__(
        self,
        edges: Sequence[Any],
        total: int,
        has_next_page: bool,
        has_previous_page: bool,
        id_field: str = "id",
    ) -> None:
        self.edges = edges
        self.total = total
        self.has_next_page = has_next_page
        self.has_previous_page = has_previous_page
        self.id_field = id_field

    def get_cursor(self, obj):
        return obj[self.id_field]

    def get_node(self, obj):
        return obj

    def get_page_info(self, connection_arguments: ConnectionArgumentsUnion):
        return {
            "hasNextPage": self.has_next_page,
            "hasPreviousPage": self.has_previous_page,
            "startCursor": self.get_cursor(self.edges[0]) if self.edges else None,
            "endCursor": self.get_cursor(self.edges[-1]) if self.edges else None,
        }

    def get_edges(self):
        return [
            {"node": self.get_node(obj), "cursor": self.get_cursor(obj)}
            for obj in self.edges
        ]
