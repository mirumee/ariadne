from io import BytesIO
from unittest.mock import ANY, call

import pytest
from graphql import get_introspection_query
from opentracing.ext import tags
from starlette.datastructures import UploadFile

from ariadne import graphql, graphql_sync
from ariadne.contrib.tracing.opentelemetry import (
    OpenTelemetryExtension,
    copy_args_for_tracing,
    opentelemetry_extension,
)
from ariadne.contrib.tracing.utils import File


@pytest.fixture
def get_tracer_mock(mocker):
    return mocker.patch("ariadne.contrib.tracing.opentelemetry.get_tracer")


@pytest.fixture
def start_as_current_span_mock(get_tracer_mock):
    return get_tracer_mock.return_value.start_as_current_span


@pytest.mark.asyncio
async def test_opentelemetry_extension_handles_async_resolvers_in_async_context(
    async_schema,
):
    _, result = await graphql(
        async_schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[OpenTelemetryExtension],
    )
    assert result == {"data": {"hello": "Hello, Bob!", "status": True}}


@pytest.mark.asyncio
async def test_opentelemetry_extension_handles_sync_resolvers_in_async_context(schema):
    _, result = await graphql(
        schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[OpenTelemetryExtension],
    )
    assert result == {"data": {"hello": "Hello, Bob!", "status": True}}


def test_opentelemetry_extension_handles_sync_resolvers_in_sync_context(schema):
    _, result = graphql_sync(
        schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[OpenTelemetryExtension],
    )
    assert result == {"data": {"hello": "Hello, Bob!", "status": True}}


@pytest.mark.asyncio
async def test_opentelemetry_extension_uses_global_tracer(schema, get_tracer_mock):
    await graphql(
        schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[OpenTelemetryExtension],
    )
    get_tracer_mock.assert_called_once()


@pytest.mark.asyncio
async def test_opentelemetry_extension_creates_span_for_query_root_in_async_context(
    async_schema, get_tracer_mock
):
    await graphql(
        async_schema, {"query": "{ status }"}, extensions=[OpenTelemetryExtension]
    )
    get_tracer_mock.return_value.start_span.assert_any_call(
        "GraphQL Operation", context=ANY
    )


def test_opentelemetry_extension_creates_span_for_query_root_in_sync_context(
    schema, get_tracer_mock
):
    graphql_sync(schema, {"query": "{ status }"}, extensions=[OpenTelemetryExtension])
    get_tracer_mock.return_value.start_span.assert_any_call(
        "GraphQL Operation", context=ANY
    )


@pytest.mark.asyncio
async def test_open_tracing_extension_sets_custom_root_span_name_from_str(
    async_schema, get_tracer_mock
):
    _, result = await graphql(
        async_schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[opentelemetry_extension(root_span_name="Custom Root Span")],
    )
    assert result == {"data": {"hello": "Hello, Bob!", "status": True}}

    get_tracer_mock.return_value.start_span.assert_any_call(
        "Custom Root Span", context=ANY
    )


@pytest.mark.asyncio
async def test_open_tracing_extension_sets_custom_root_span_name_from_callable(
    async_schema, get_tracer_mock
):
    def get_root_span_name(_):
        return "Callable Root Span"

    _, result = await graphql(
        async_schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[opentelemetry_extension(root_span_name=get_root_span_name)],
    )
    assert result == {"data": {"hello": "Hello, Bob!", "status": True}}

    get_tracer_mock.return_value.start_span.assert_any_call(
        "Callable Root Span", context=ANY
    )


@pytest.mark.asyncio
async def test_opentelemetry_extension_creates_span_for_field_in_async_context(
    async_schema, start_as_current_span_mock
):
    await graphql(
        async_schema, {"query": "{ status }"}, extensions=[OpenTelemetryExtension]
    )
    start_as_current_span_mock.assert_any_call("status", context=ANY)


def test_opentelemetry_extension_creates_span_for_field_in_sync_context(
    schema, start_as_current_span_mock
):
    graphql_sync(schema, {"query": "{ status }"}, extensions=[OpenTelemetryExtension])
    start_as_current_span_mock.assert_any_call("status", context=ANY)


@pytest.mark.asyncio
async def test_opentelemetry_extension_sets_graphql_component_tag_on_root_span_in_async(
    async_schema, get_tracer_mock
):
    await graphql(
        async_schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[OpenTelemetryExtension],
    )

    get_tracer_mock.return_value.start_span.return_value.set_attribute.assert_called_once_with(
        tags.COMPONENT, "GraphQL"
    )


def test_opentelemetry_extension_sets_graphql_component_tag_on_root_span_in_sync(
    schema, get_tracer_mock
):
    graphql_sync(
        schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[OpenTelemetryExtension],
    )
    get_tracer_mock.return_value.start_span.return_value.set_attribute.assert_called_once_with(
        tags.COMPONENT, "GraphQL"
    )


@pytest.mark.asyncio
async def test_opentelemetry_extension_calls_custom_arg_filter_in_async_context(
    async_schema, mocker
):
    arg_filter = mocker.Mock(return_value={})
    await graphql(
        async_schema,
        {"query": '{ hello(name: "Bob") }'},
        extensions=[opentelemetry_extension(arg_filter=arg_filter)],
    )
    arg_filter.assert_called_once_with({"name": "Bob"}, ANY)


def test_opentelemetry_extension_calls_custom_arg_filter_in_sync_context(
    schema, mocker
):
    arg_filter = mocker.Mock(return_value={})
    graphql_sync(
        schema,
        {"query": '{ hello(name: "Bob") }'},
        extensions=[opentelemetry_extension(arg_filter=arg_filter)],
    )
    arg_filter.assert_called_once_with({"name": "Bob"}, ANY)


@pytest.mark.asyncio
async def test_opentelemetry_extension_sets_filtered_args_on_span_in_async_context(
    async_schema, start_as_current_span_mock, mocker
):
    arg_filter = mocker.Mock(return_value={"name": "[filtered]"})
    await graphql(
        async_schema,
        {"query": '{ hello(name: "Bob") }'},
        extensions=[opentelemetry_extension(arg_filter=arg_filter)],
    )

    span_mock = start_as_current_span_mock.return_value.__enter__.return_value
    span_mock.set_attribute.assert_has_calls(
        [
            call("component", "GraphQL"),
            call("graphql.operation.name", "GraphQL Operation"),
            call("graphql.parentType", "Query"),
            call("graphql.path", "hello"),
            call("graphql.arg[name]", "[filtered]"),
        ]
    )


def test_opentelemetry_extension_sets_filtered_args_on_span_in_sync_context(
    schema, start_as_current_span_mock, mocker
):
    arg_filter = mocker.Mock(return_value={"name": "[filtered]"})
    graphql_sync(
        schema,
        {"query": '{ hello(name: "Bob") }'},
        extensions=[opentelemetry_extension(arg_filter=arg_filter)],
    )

    span_mock = start_as_current_span_mock.return_value.__enter__.return_value
    span_mock.set_attribute.assert_has_calls(
        [
            call("component", "GraphQL"),
            call("graphql.operation.name", "GraphQL Operation"),
            call("graphql.parentType", "Query"),
            call("graphql.path", "hello"),
            call("graphql.arg[name]", "[filtered]"),
        ]
    )


@pytest.mark.asyncio
async def test_opentelemetry_extension_sets_filtered_args_on_span_in_combined_context(
    combined_schema, start_as_current_span_mock, mocker
):
    arg_filter = mocker.Mock(return_value={"name": "[filtered]"})
    await graphql(
        combined_schema,
        {"query": '{ hello(name: "Bob") }'},
        extensions=[opentelemetry_extension(arg_filter=arg_filter)],
    )

    span_mock = start_as_current_span_mock.return_value.__enter__.return_value
    span_mock.set_attribute.assert_has_calls(
        [
            call("component", "GraphQL"),
            call("graphql.operation.name", "GraphQL Operation"),
            call("graphql.parentType", "Query"),
            call("graphql.path", "hello"),
            call("graphql.arg[name]", "[filtered]"),
        ]
    )


@pytest.mark.asyncio
async def test_opentelemetry_extension_handles_error_in_async_resolver_in_async_context(
    async_schema,
):
    _, result = await graphql(
        async_schema,
        {"query": "{ testError status }"},
        extensions=[OpenTelemetryExtension],
    )
    assert result["data"] == {"testError": None, "status": True}


@pytest.mark.asyncio
async def test_opentelemetry_extension_handles_error_in_sync_resolver_in_async_context(
    schema,
):
    _, result = await graphql(
        schema, {"query": "{ testError status }"}, extensions=[OpenTelemetryExtension]
    )
    assert result["data"] == {"testError": None, "status": True}


def test_opentelemetry_extension_handles_errors_in_resolver_in_sync_context(schema):
    _, result = graphql_sync(
        schema, {"query": "{ testError status }"}, extensions=[OpenTelemetryExtension]
    )
    assert result["data"] == {"testError": None, "status": True}


@pytest.mark.asyncio
async def test_opentelemetry_extension_handles_error_in_combined_context(
    combined_schema,
):
    _, result = await graphql(
        combined_schema,
        {"query": "{ testError status }"},
        extensions=[OpenTelemetryExtension],
    )
    assert result["data"] == {"testError": None, "status": True}


@pytest.mark.asyncio
async def test_opentelemetry_extension_doesnt_break_introspection(schema):
    introspection_query = get_introspection_query(descriptions=True)
    _, result = await graphql(
        schema, {"query": introspection_query}, extensions=[OpenTelemetryExtension]
    )
    assert "errors" not in result


@pytest.mark.asyncio
async def test_resolver_args_filter_handles_uploaded_files_from_asgi(mocker):
    def arg_filter(args, _):
        return args

    file_size = 1024 * 1024
    extension = OpenTelemetryExtension(arg_filter=arg_filter)
    file_ = UploadFile(
        BytesIO(),
        size=0,
        filename="test",
        headers={"content-type": "application/json"},
    )
    await file_.write(b"\0" * file_size)
    kwargs = {"0": file_}
    info = mocker.Mock()

    copied_kwargs = extension.filter_resolver_args(kwargs, info)
    assert (
        f"<class 'starlette.datastructures.UploadFile'>"
        f"(mime_type={file_.content_type}, size={file_size}, filename={file_.filename})"
    ) == copied_kwargs["0"]


class MockFile(File):
    def __init__(self, file_name, size):
        self._file_name = file_name
        self._size = size

    @property
    def size(self):
        return self._size


def test_resolver_args_filter_handles_uploaded_files_from_wsgi(mocker):
    def arg_filter(args, _):
        return args

    extension = OpenTelemetryExtension(arg_filter=arg_filter)
    test_file = MockFile("hello.txt", 2137)

    kwargs = {"0": test_file}
    info = mocker.Mock()

    copied_kwargs = extension.filter_resolver_args(kwargs, info)
    assert (
        "<class 'tests.tracing.test_opentelemetry.MockFile'>"
        "(mime_type=not/available, size=2137, filename=hello.txt)"
    ) == copied_kwargs["0"]


def test_resolver_args_with_uploaded_files_from_wsgi_are_copied_for_tracing():
    file_1 = MockFile("hello.txt", 21)
    file_2 = MockFile("other.txt", 37)

    test_dict = {
        "a": 10,
        "b": [1, 2, 3, {"hehe": {"Hello": 10}}],
        "c": file_1,
        "d": {"ee": ["zz", [10, 10, 10], file_2]},
    }
    result = copy_args_for_tracing(test_dict)
    assert {
        "a": 10,
        "b": [1, 2, 3, {"hehe": {"Hello": 10}}],
        "c": (
            "<class 'tests.tracing.test_opentelemetry.MockFile'>"
            "(mime_type=not/available, size=21, filename=hello.txt)"
        ),
        "d": {
            "ee": [
                "zz",
                [
                    10,
                    10,
                    10,
                ],
                (
                    "<class 'tests.tracing.test_opentelemetry.MockFile'>"
                    "(mime_type=not/available, size=37, filename=other.txt)"
                ),
            ],
        },
    } == result
