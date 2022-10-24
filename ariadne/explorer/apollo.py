from .explorer import Explorer
from .template import read_template, render_template

APOLLO_HTML = read_template("apollo_sandbox.html")

DEFAULT_QUERY = "# Write your query or mutation here"


class ExplorerApollo(Explorer):
    def __init__(
        self,
        title: str = "Ariadne GraphQL",
        default_query: str = DEFAULT_QUERY,
    ):
        self.parsed_html = render_template(
            APOLLO_HTML,
            {
                "title": title,
                "default_query": default_query.replace("\n", "\\n"),
            },
        )

    def html(self, _):
        return self.parsed_html
