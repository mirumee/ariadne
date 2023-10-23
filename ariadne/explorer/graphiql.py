from .default_query import escape_default_query
from .explorer import Explorer
from .template import read_template, render_template

GRAPHIQL_HTML = read_template("graphiql.html")

DEFAULT_QUERY = """#
# GraphiQL is an in -browser tool for writing, validating, and
# testing GraphQL queries.
#
# Type queries into this side of the screen, and you will see intelligent
# typeaheads aware of the current GraphQL type schema and live syntax and
# validation errors highlighted within the text.
#
# GraphQL queries typically start with a "{" character. Lines that start
# with a # are ignored.
#
# An example GraphQL query might look like:
#
#     {
#       field(arg: "value") {
#         subField
#
#       }
#
#     }
#
# Keyboard shortcuts:
#
#   Prettify query: Shift - Ctrl - P(or press the prettify button)
#
#  Merge fragments: Shift - Ctrl - M(or press the merge button)
#
#        Run Query: Ctrl - Enter(or press the play button)
#
#    Auto Complete: Ctrl - Space(or just start typing)
#"""


class ExplorerGraphiQL(Explorer):
    def __init__(
        self,
        title: str = "Ariadne GraphQL",
        explorer_plugin: bool = False,
        default_query: str = DEFAULT_QUERY,
        subscription_url: str = "",
    ) -> None:
        self.parsed_html = render_template(
            GRAPHIQL_HTML,
            {
                "title": title,
                "enable_explorer_plugin": explorer_plugin,
                "default_query": escape_default_query(default_query),
                "subscription_url": subscription_url,
            },
        )

    def html(self, _):
        return self.parsed_html
