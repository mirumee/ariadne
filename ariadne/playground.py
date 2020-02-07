from dataclasses import dataclass
from enum import Enum
import json
from typing import Optional, Dict


class RequestCredentials(Enum):
    OMIT = "omit"
    INCLUDE = "include"
    SAME_ORIGIN = "same-origin"


class EditorTheme(Enum):
    LIGHT = "light"
    DARK = "dark"


class CursorShape(Enum):
    LINE = "line"
    BLOCK = "block"
    UNDERLINE = "underline"


@dataclass(frozen=True)
class ISettings:
    editor_cursor_shape: Optional[CursorShape] = None
    editor_font_family: Optional[str] = None
    editor_font_size: Optional[int] = None
    editor_reuse_headers: Optional[bool] = None
    editor_theme: EditorTheme = None
    general_beta_updates: bool = None
    prettier_print_width: int = None
    prettier_tab_width: int = None
    prettier_use_tabs: bool = None
    request_credentials: RequestCredentials = None
    schema_disable_comments: bool = None
    schema_polling_enable: bool = None
    schema_polling_endpoint_filter: str = None
    schema_polling_interval: int = None
    tracing_hide_tracing_response: bool = None

    def to_json(self):
        raw_dict = {
            "editor.cursorShape": self.editor_cursor_shape,
            "editor.fontFamily": self.editor_font_family,
            "editor.fontSize": self.editor_font_size,
            "editor.reuseHeaders": self.editor_reuse_headers,
            "editor.theme": self.editor_theme.value if self.editor_theme is not None else None,
            "general.betaUpdates": self.general_beta_updates,
            "prettier.printWidth": self.prettier_print_width,
            "prettier.tabWidth": self.prettier_tab_width,
            "prettier.useTabs": self.prettier_use_tabs,
            "request.credentials": self.request_credentials.value if self.request_credentials is not None else None,
            "schema.disableComments": self.schema_disable_comments,
            "schema.polling.enable": self.schema_polling_enable,
            "schema.polling.endpointFilter": self.schema_polling_endpoint_filter,
            "schema.polling.interval": self.schema_polling_interval,
            "tracing.hideTracingResponse": self.tracing_hide_tracing_response
        }
        return {k: v for k, v in raw_dict.items() if v is not None}


@dataclass(frozen=True)
class PlaygroundSettings:
    settings: Optional[ISettings] = None
    share_enabled: Optional[str] = None
    workpace_name: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


def generate_playground_options(settings: PlaygroundSettings = None):
    raw_dict = {
        "settings": settings.settings.to_json(),
        "shareEnabled": settings.share_enabled,
        "workspaceName": settings.workpace_name,
        "headers": settings.headers,
    }
    _dict = {k: v for k, v in raw_dict.items() if v is not None}
    return ",\n".join([
        f"{k}: {json.dumps(v)}" for k,v in _dict.items()
    ])
