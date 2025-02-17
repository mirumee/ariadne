import json
from typing import Optional, Union

from .explorer import Explorer
from .template import read_template, render_template

PLAYGROUND_HTML = read_template("playground.html")

SettingsDict = dict[str, Union[str, int, bool, dict[str, str]]]


class ExplorerPlayground(Explorer):
    def __init__(
        self,
        title: str = "Ariadne GraphQL",
        share_enabled: bool = False,
        editor_cursor_shape: Optional[str] = None,
        editor_font_family: Optional[str] = None,
        editor_font_size: Optional[int] = None,
        editor_reuse_headers: Optional[bool] = None,
        editor_theme: Optional[str] = None,
        general_beta_updates: Optional[bool] = None,
        prettier_print_width: Optional[int] = None,
        prettier_tab_width: Optional[int] = None,
        prettier_use_tabs: Optional[bool] = None,
        request_credentials: Optional[str] = None,
        request_global_headers: Optional[dict[str, str]] = None,
        schema_polling_enable: Optional[bool] = None,
        schema_polling_endpoint_filter: Optional[str] = None,
        schema_polling_interval: Optional[int] = None,
        schema_disable_comments: Optional[bool] = None,
        tracing_hide_tracing_response: Optional[bool] = None,
        tracing_tracing_supported: Optional[bool] = None,
        query_plan_hide_query_plan_response: Optional[bool] = None,
    ) -> None:
        settings = self.build_settings(
            editor_cursor_shape=editor_cursor_shape,
            editor_font_family=editor_font_family,
            editor_font_size=editor_font_size,
            editor_reuse_headers=editor_reuse_headers,
            editor_theme=editor_theme,
            general_beta_updates=general_beta_updates,
            prettier_print_width=prettier_print_width,
            prettier_tab_width=prettier_tab_width,
            prettier_use_tabs=prettier_use_tabs,
            request_credentials=request_credentials,
            request_global_headers=request_global_headers,
            schema_polling_enable=schema_polling_enable,
            schema_polling_endpoint_filter=schema_polling_endpoint_filter,
            schema_polling_interval=schema_polling_interval,
            schema_disable_comments=schema_disable_comments,
            tracing_hide_tracing_response=tracing_hide_tracing_response,
            tracing_tracing_supported=tracing_tracing_supported,
            query_plan_hide_query_plan_response=query_plan_hide_query_plan_response,
        )

        self.parsed_html = render_template(
            PLAYGROUND_HTML,
            {
                "title": title,
                "settings": json.dumps(settings) if settings else None,
                "share_enabled": str(share_enabled).lower(),
            },
        )

    def build_settings(  # noqa: C901
        self,
        editor_cursor_shape: Optional[str] = None,
        editor_font_family: Optional[str] = None,
        editor_font_size: Optional[int] = None,
        editor_reuse_headers: Optional[bool] = None,
        editor_theme: Optional[str] = None,
        general_beta_updates: Optional[bool] = None,
        prettier_print_width: Optional[int] = None,
        prettier_tab_width: Optional[int] = None,
        prettier_use_tabs: Optional[bool] = None,
        request_credentials: Optional[str] = None,
        request_global_headers: Optional[dict[str, str]] = None,
        schema_polling_enable: Optional[bool] = None,
        schema_polling_endpoint_filter: Optional[str] = None,
        schema_polling_interval: Optional[int] = None,
        schema_disable_comments: Optional[bool] = None,
        tracing_hide_tracing_response: Optional[bool] = None,
        tracing_tracing_supported: Optional[bool] = None,
        query_plan_hide_query_plan_response: Optional[bool] = None,
    ) -> SettingsDict:
        settings: SettingsDict = {}
        if editor_cursor_shape:
            settings["editor.cursorShape"] = editor_cursor_shape
        if editor_font_family:
            settings["editor.fontFamily"] = editor_font_family
        if editor_font_size:
            settings["editor.fontSize"] = editor_font_size
        if editor_reuse_headers is not None:
            settings["editor.reuseHeaders"] = editor_reuse_headers
        if editor_theme:
            settings["editor.theme"] = editor_theme
        if general_beta_updates is not None:
            settings["general.betaUpdates"] = general_beta_updates
        if prettier_print_width:
            settings["prettier.printWidth"] = prettier_print_width
        if prettier_tab_width:
            settings["prettier.tabWidth"] = prettier_tab_width
        if prettier_use_tabs is not None:
            settings["prettier.useTabs"] = prettier_use_tabs
        if request_credentials:
            settings["request.credentials"] = request_credentials
        if request_global_headers:
            settings["request.globalHeaders"] = request_global_headers
        if schema_polling_enable is not None:
            settings["schema.polling.enable"] = schema_polling_enable
        if schema_polling_endpoint_filter:
            settings["schema.polling.endpointFilter"] = schema_polling_endpoint_filter
        if schema_polling_interval:
            settings["schema.polling.interval"] = schema_polling_interval
        if schema_disable_comments is not None:
            settings["schema.disableComments"] = schema_disable_comments
        if tracing_hide_tracing_response is not None:
            settings["tracing.hideTracingResponse"] = tracing_hide_tracing_response
        if tracing_tracing_supported is not None:
            settings["tracing.tracingSupported"] = tracing_tracing_supported
        if query_plan_hide_query_plan_response is not None:
            settings["queryPlan.hideQueryPlanResponse"] = (
                query_plan_hide_query_plan_response
            )

        return settings

    def html(self, _):
        return self.parsed_html
