from ariadne.api_explorer import (
    APIExplorerGraphiQL,
    APIExplorerHttp405,
    APIExplorerPlayground,
)


def test_graphiql_explorer_produces_html(snapshot):
    explorer = APIExplorerGraphiQL()
    snapshot.assert_match(explorer.html(None))


def test_playground_explorer_produces_html(snapshot):
    explorer = APIExplorerPlayground()
    snapshot.assert_match(explorer.html(None))


def test_http_405_explorer_doesnt_produce_html():
    explorer = APIExplorerHttp405()
    assert explorer.html(None) is None
