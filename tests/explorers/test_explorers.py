import pytest

from ariadne.explorer import (
    ExplorerApollo,
    ExplorerGraphiQL,
    ExplorerHttp405,
    ExplorerPlayground,
)


def test_apollo_explorer_produces_html(snapshot):
    explorer = ExplorerApollo()
    assert snapshot == explorer.html(None)


def test_graphiql_explorer_produces_html(snapshot):
    explorer = ExplorerGraphiQL()
    assert snapshot == explorer.html(None)


@pytest.mark.parametrize("include_cookies", [True, False, None])
def test_apollo_explorer_includes_cookies_setting(snapshot, include_cookies):
    explorer = ExplorerApollo(
        **({"include_cookies": include_cookies} if include_cookies is not None else {})
    )
    assert snapshot == explorer.html(None)


def test_graphiql_explorer_includes_explorer_plugin(snapshot):
    explorer = ExplorerGraphiQL(explorer_plugin=True)
    assert snapshot == explorer.html(None)


def test_graphiql_explorer_with_custom_subscription_url(snapshot):
    explorer = ExplorerGraphiQL(subscription_url="ws://custom_url")
    assert snapshot == explorer.html(None)


def test_playground_explorer_produces_html(snapshot):
    explorer = ExplorerPlayground()
    assert snapshot == explorer.html(None)


def test_playground_explorer_produces_html_with_settings(snapshot):
    explorer = ExplorerPlayground(
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
    assert snapshot == explorer.html(None)


def test_http_405_explorer_doesnt_produce_html():
    explorer = ExplorerHttp405()
    assert explorer.html(None) is None
