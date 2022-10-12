from .explorer import Explorer
from .template import read_template, render_template

GRAPHIQL_HTML = read_template("graphiql.html")


class ExplorerGraphiQL(Explorer):
    def __init__(
        self,
        title: str = "Ariadne GraphQL",
        explorer_plugin: bool = False,
    ):
        self.parsed_html = render_template(
            GRAPHIQL_HTML,
            {
                "title": title,
                "enable_explorer_plugin": explorer_plugin,
            },
        )

    def html(self, _):
        return self.parsed_html
