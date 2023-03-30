from io import BytesIO
from unittest.mock import ANY, call

import pytest
from graphql import get_introspection_query
from opentracing.ext import tags
from starlette.datastructures import UploadFile

from ariadne import graphql
from ariadne.contrib.tracing.opentracing import (
    OpenTracingExtension,
    opentracing_extension,
)


@pytest.fixture
def global_tracer_mock(mocker):
    return mocker.patch("ariadne.contrib.tracing.opentracing.global_tracer")


@pytest.fixture
def should_trace_mock(mocker):
    return mocker.patch("ariadne.contrib.tracing.opentracing.should_trace")


@pytest.fixture
def active_span_mock(global_tracer_mock):
    return global_tracer_mock.return_value.start_active_span.return_value


@pytest.mark.asyncio
async def test_opentracing_extension_causes_no_errors_in_query_execution(schema):
    _, result = await graphql(
        schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[OpenTracingExtension],
    )
    assert result == {"data": {"hello": "Hello, Bob!", "status": True}}


@pytest.mark.asyncio
async def test_opentracing_extension_uses_global_tracer(schema, global_tracer_mock):
    await graphql(
        schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[OpenTracingExtension],
    )
    global_tracer_mock.assert_called_once()


@pytest.mark.asyncio
async def test_opentracing_extension_creates_span_for_query_root(
    schema, global_tracer_mock
):
    await graphql(schema, {"query": "{ status }"}, extensions=[OpenTracingExtension])
    global_tracer_mock.return_value.start_active_span.assert_any_call("GraphQL Query")


@pytest.mark.asyncio
async def test_opentracing_extension_creates_span_for_field(schema, global_tracer_mock):
    await graphql(schema, {"query": "{ status }"}, extensions=[OpenTracingExtension])
    global_tracer_mock.return_value.start_active_span.assert_any_call("status")


@pytest.mark.asyncio
async def test_opentracing_extension_sets_graphql_component_tag_on_root_span(
    schema, active_span_mock
):
    await graphql(
        schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[OpenTracingExtension],
    )
    active_span_mock.span.set_tag.assert_called_once_with(tags.COMPONENT, "graphql")


@pytest.mark.asyncio
async def test_opentracing_extension_calls_custom_arg_filter(schema, mocker):
    arg_filter = mocker.Mock(return_value={})
    await graphql(
        schema,
        {"query": '{ hello(name: "Bob") }'},
        extensions=[opentracing_extension(arg_filter=arg_filter)],
    )
    arg_filter.assert_called_once_with({"name": "Bob"}, ANY)


@pytest.mark.asyncio
async def test_opentracing_extension_sets_filtered_args_on_span(
    schema, active_span_mock, mocker
):
    arg_filter = mocker.Mock(return_value={"name": "[filtered]"})
    await graphql(
        schema,
        {"query": '{ hello(name: "Bob") }'},
        extensions=[opentracing_extension(arg_filter=arg_filter)],
    )

    span_mock = active_span_mock.__enter__.return_value.span
    span_mock.set_tag.assert_has_calls(
        [
            call("component", "graphql"),
            call("graphql.parentType", "Query"),
            call("graphql.path", "hello"),
            call("graphql.param.name", "[filtered]"),
        ]
    )


@pytest.mark.asyncio
async def test_opentracing_extension_calls_custom_should_trace_if_passed(
    schema, mocker, should_trace_mock
):
    should_trace = mocker.Mock(return_value={})
    await graphql(
        schema,
        {"query": '{ hello(name: "Bob") }'},
        extensions=[opentracing_extension(should_trace=should_trace)],
    )
    should_trace_mock.assert_not_called()
    should_trace.assert_called_once_with(ANY)


@pytest.mark.asyncio
async def test_opentracing_extension_calls_default_should_trace_if_not_passed(
    schema, should_trace_mock
):
    await graphql(
        schema,
        {"query": '{ hello(name: "Bob") }'},
        extensions=[opentracing_extension()],
    )
    should_trace_mock.assert_called_once_with(ANY)


@pytest.mark.asyncio
async def test_opentracing_extension_doesnt_create_span_if_custom_should_trace_returns_false(
    schema, active_span_mock
):
    def should_trace(info):
        return info.field_name == "status"

    await graphql(
        schema,
        {"query": '{ hello(name: "Bob") status }'},
        extensions=[opentracing_extension(should_trace=should_trace)],
    )

    span_mock = active_span_mock.__enter__.return_value.span
    span_mock.set_tag.assert_has_calls(
        [
            call("component", "graphql"),
            call("graphql.parentType", "Query"),
            call("graphql.path", "status"),
        ]
    )
    assert call("graphql.path", "hello") not in span_mock.set_tag.mock_calls


@pytest.mark.asyncio
async def test_opentracing_extension_handles_errors_in_resolvers(schema):
    _, result = await graphql(
        schema, {"query": "{ testError status }"}, extensions=[OpenTracingExtension]
    )
    assert result["data"] == {"testError": None, "status": True}


@pytest.mark.asyncio
async def test_opentracing_extension_doesnt_break_introspection(schema):
    introspection_query = get_introspection_query(descriptions=True)
    _, result = await graphql(
        schema, {"query": introspection_query}, extensions=[OpenTracingExtension]
    )
    assert "errors" not in result


@pytest.mark.asyncio
async def test_resolver_args_filter_handles_uploaded_files_from_asgi(mocker):
    def arg_filter(args, _):
        return args

    file_size = 1024 * 1024
    extension = OpenTracingExtension(arg_filter=arg_filter)
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
