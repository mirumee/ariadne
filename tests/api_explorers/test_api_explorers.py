from ariadne.api_explorer import (
    APIExplorerGraphiQL,
    APIExplorerHttp405,
    APIExplorerPlayground,
)


def test_graphiql_explorer_produces_html(snapshot):
    explorer = APIExplorerGraphiQL()
    snapshot.assert_match(explorer.html(None))


def test_graphiql_explorer_includes_explorer_plugin(snapshot):
    explorer = APIExplorerGraphiQL(explorer_plugin=True)
    snapshot.assert_match(explorer.html(None))


def test_playground_explorer_produces_html(snapshot):
    explorer = APIExplorerPlayground()
    snapshot.assert_match(explorer.html(None))


def test_playground_explorer_produces_html_with_settings(snapshot):
    explorer = APIExplorerPlayground(
        title="Hello world!",
        editor_cursor_shape="block",
        editor_font_family="helvetica",
        editor_font_size=24,
        editor_reuse_headers=True,
        editor_theme="light",
        general_beta_updates=False,
        prettier_print_width=4,
        prettier_tab_width=4,
        prettier_use_tabs=True,
        request_credentials="same-origin",
        request_global_headers={"hum": "test"},
        schema_polling_enable=True,
        schema_polling_endpoint_filter="*domain*",
        schema_polling_interval=4200,
        schema_disable_comments=True,
        tracing_hide_tracing_response=True,
        tracing_tracing_supported=True,
        query_plan_hide_query_plan_response=True,
    )
    snapshot.assert_match(explorer.html(None))


def test_http_405_explorer_doesnt_produce_html():
    explorer = APIExplorerHttp405()
    assert explorer.html(None) is None
