from .api_explorer import APIExplorer
from .template import read_template, render_template

PLAYGROUND_HTML = read_template("playground.html")


class APIExplorerPlayground(APIExplorer):
    def __init__(
        self,
        title: str = "Ariadne GraphQL",
    ):
        self.parsed_html = render_template(
            PLAYGROUND_HTML,
            {"title": title},
        )

    def html(self, _):
        return self.parsed_html
