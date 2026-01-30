---
id: explorers
title: GraphQL explorers
---

Explorers provide web-based GUI for interacting with your GraphQL API. Ariadne implements support for multiple explorers out of the box. It also supports disabling explorer UI altogether.

Ariadne also makes it possible for developers to [implement custom support for any explorer](#custom-explorer).


## GraphiQL 2

```python
from ariadne.explorer import ExplorerGraphiQL
```

Default GraphQL explorer in Ariadne since 0.17 release.


### Supported options

`ExplorerGraphiQL` constructor accepts following options:

- `title: str = "Ariadne GraphQL"` - Used for page title and loading message.
- `default_query: str = "..."` - Default content of editor area.
- `explorer_plugin: bool = False` - Enables [GraphQL Explorer plugin](https://www.youtube.com/watch?v=8DmtCPX4tdo&nounroll=1).
- `subscription_url: str = ""` - URL to use by GraphQL subscription connections. Defaults to current URL, but with `http` protocol replaced with `ws`.


## Apollo Sandbox

```python
from ariadne.explorer import ExplorerApollo
```

Embedded Apollo Sandbox.


### Supported options

`ExplorerApollo` constructor accepts following options:

- `title: str = "Ariadne GraphQL"` - Used for page title and loading message.
- `default_query: str = "..."` - Default content of editor area.
- `include_cookies: bool: bool = False` - Controls if Apollo explorer should include cookies in requests.


## GraphQL Playground

```python
from ariadne.explorer import ExplorerPlayground
```

GraphQL Playground was default explorer in Ariadne until 0.17 release. **It's no longer maintained**. with its features being merged in to GraphiQL 2. It's provided by Ariadne as an alternative for teams and projects that don't want to make a switch yet.


### Supported options

`ExplorerPlayground` constructor accepts following options:

- `title: str = "Ariadne GraphQL"` - Used for page title and loading message.
- `share_enabled: bool = False` - Controls share playground feature.
- `editor_cursor_shape: Optional[str] = None` - Controls `editor.cursorShape` setting (defaults to `"line"`, can be changed to `"block"` or `"underline"`).
- `editor_font_family: Optional[str] = None` - Controls `editor.fontFamily` setting (defaults to `"'Source Code Pro', 'Consolas', 'Inconsolata', 'Droid Sans Mono', 'Monaco', monospace"`).
- `editor_font_size: Optional[int] = None` - Controls `editor.fontSize` setting (defaults to `14`).
- `editor_reuse_headers: Optional[bool] = None` - Controls `editor.reuseHeaders` setting (`true` by default).
- `editor_theme: Optional[str] = None` - Controls `editor.theme` setting (`"dark"` by default, can be changed to `"light"`).
- `general_beta_updates: Optional[bool] = None` - Controls `general.betaUpdates` setting (`false` by default).
- `prettier_print_width: Optional[int] = None` - Controls `prettier.printWidth` setting (`80` by default).
- `prettier_tab_width: Optional[int] = None` - Controls `prettier.tabWidth` setting (`2` by default).
- `prettier_use_tabs: Optional[bool] = None` - Controls `prettier.useTabs` setting (`false` by default).
- `request_credentials: Optional[str] = None` - Controls `request.credentials` setting (`"omit"` by default, can be changed to `"include"` or `"same-origin"`).
- `request_global_headers: Optional[Dict[str, str]] = None` - Controls `request.globalHeaders` setting (`{}` by default).
- `schema_polling_enable: Optional[bool] = None` - Controls `schema.polling.enable` setting (`true` by default).
- `schema_polling_endpoint_filter: Optional[str] = None` - Controls `schema.polling.endpointFilter` setting (defaults to `"*localhost*"`).
- `schema_polling_interval: Optional[int] = None` - Controls `schema.polling.interval` setting (defaults to `2000`).
- `schema_disable_comments: Optional[bool] = None` - Controls `schema.disableComments` setting (defaults to `true`).
- `tracing_hide_tracing_response: Optional[bool] = None` - Controls `tracing.hideTracingResponse` setting (`false` by default).
- `tracing_tracing_supported: Optional[bool] = None` - Controls `tracing.tracingSupported` setting (`true` by default).
- `query_plan_hide_query_plan_response: Optional[bool] = None` - Controls `query.plan.hideQueryPlanResponse` setting (`false` by default).

See Playground's readme for [complete reference of its settings](https://github.com/graphql/graphql-playground#settings).


## ExplorerHttp405

```python
from ariadne.explorer import ExplorerHttp405
```

This explorer always triggers HTTP 405 "method not allowed" response from Ariadne, serving as a way to disable GraphQL explorer.


## Custom explorer

You can implement custom GraphQL explorer for Ariadne. All explorers should extend `Explorer` base class importable from `ariadne.explorer`:

```python
from ariadne.explorer import Explorer


class MyExplorer(Explorer):
    ...
```

Explorer class needs to implement `html` method taking single argument, "request" instance specific to used HTTP protocol implementation. This method should return HTML code for explorer, or `None`:

```python
from ariadne.explorer import Explorer


class MyExplorer(Explorer):
    def html(self, request):
        return "<div>Hello world</div>"
```

If `html` method returns `None`, HTTP 405 "method not allowed" error will be returned by the HTTP server:

```python
from ariadne.explorer import Explorer


class MyExplorer(Explorer):
    def html(self, request):
        if not request.user.is_staff:
            return None

        return "<div>Hello world</div>"
```

Some HTTP servers implemented by Ariadne (eg. `ariadne.asgi.GraphQL`) also support `html` returning awaitable:

```python
from ariadne.explorer import Explorer
from myapp.auth import get_authorized_user


class MyExplorer(Explorer):
    def html(self, request):
        return self.html_future(request)
    
    async def html_future(self, request)
        auth_token = request.headers.get("authorization")
        if not request.headers.get("authorization"):
            return None

        if not await get_authorized_user(request, auth_token):
            return None

        return "<div>Hello world</div>"
```


### `render_template`

Ariadne implements minimal template engine for use by explorers. This engine is available through the `render_template` utility function importable from `ariadne.explorer`. It takes template string (inspired by Django) and returns final string with values and blocks evaluated:

```python
import json
from ariadne.explorer import render_template

template = "Hello {% if name %}{{ name }}{% else %}guest{% endif %}!"

result = render_template(template, {"name": "Alic<3"})
assert result == "Hello Alic&lt;3!"

result_2 = render_template(template)
assert result_2 == "Hello guest!"
```

`if` and `ifnot` blocks can be used for conditions. Those take one or more variable names (separated by space) and require all of them to be true for `if` and false for `ifnot`:

```python
import json
from ariadne.explorer import render_template

template = """
Hello {% if name %}{{ name }}{% else %}guest{% endif %}!

You are {% ifnot admin %}a member{% else %}an admin{% endif %}.

Your level is {% if admin moderator %}staff{% else %}member{% endif %}.
"""

result = render_template(
    template,
    {
        "name": "Alic<3",
        "admin" False,
        "moderator", False,
    },
)

assert result == """
Hello Alic&lt;3!

You are a member.

Your level is member.
"""
```

Values are escaped on render. Use `{% raw value_name %}` to render unfiltered values:

```python
import json
from ariadne.explorer import render_template

template = """
<script>
const value = {% raw safe_value %};
</script>
"""

result = render_template(
    template,
    {
        "safe_value": json.dumps({"a": "b"}),
    },
)

assert result == """
<script>
const value = {"a": "b"};
</script>
"""