import html

from .api_explorer import APIExplorer
from .template import read_template, render_template

GRAPHIQL_HTML = read_template("graphiql.html")


class APIExplorerGraphiQL(APIExplorer):
    def __init__(
        self,
        title: str = "Ariadne GraphQL",
        explorer_plugin: bool = False,
    ):
        self.parsed_html = render_template(
            GRAPHIQL_HTML,
            {
                "title": html.escape(title),
                "enable_explorer_plugin": explorer_plugin,
            },
        )

    def html(self, _):
        return self.parsed_html
