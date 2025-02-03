from typing import Sequence

from typing_extensions import Any

from ariadne.contrib.relay.arguments import ConnectionArgumentsUnion


class RelayConnection:
    def __init__(
        self,
        edges: Sequence[Any],
        total: int,
        has_next_page: bool,
        has_previous_page: bool,
    ) -> None:
        self.edges = edges
        self.total = total
        self.has_next_page = has_next_page
        self.has_previous_page = has_previous_page

    def get_cursor(self, node):
        return node["id"]

    def get_page_info(
        self, connection_arguments: ConnectionArgumentsUnion
    ):  # pylint: disable=unused-argument
        return {
            "hasNextPage": self.has_next_page,
            "hasPreviousPage": self.has_previous_page,
            "startCursor": self.get_cursor(self.edges[0]) if self.edges else None,
            "endCursor": self.get_cursor(self.edges[-1]) if self.edges else None,
        }

    def get_edges(self):
        return [{"node": node, "cursor": self.get_cursor(node)} for node in self.edges]
