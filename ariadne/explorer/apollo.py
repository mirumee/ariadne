from .default_query import escape_default_query
from .explorer import Explorer
from .template import read_template, render_template

APOLLO_HTML = read_template("apollo_sandbox.html")

DEFAULT_QUERY = "# Write your query or mutation here"


class ExplorerApollo(Explorer):
    def __init__(
        self,
        title: str = "Ariadne GraphQL",
        default_query: str = DEFAULT_QUERY,
        include_cookies: bool = False,
    ) -> None:
        self.parsed_html = render_template(
            APOLLO_HTML,
            {
                "title": title,
                "default_query": escape_default_query(default_query),
                "include_cookies": "true" if include_cookies else "false",
            },
        )

    def html(self, _):
        return self.parsed_html
