from unittest.mock import ANY, call

import pytest
from graphql import get_introspection_query
from opentracing.ext import tags

from ariadne import graphql_sync as graphql
from ariadne.contrib.tracing.opentracing import (
    OpenTracingExtensionSync as OpenTracingExtension,
)
from ariadne.contrib.tracing.opentracing import (
    opentracing_extension_sync as opentracing_extension,
)
from ariadne.contrib.tracing.opentracing import File, copy_args_for_tracing


@pytest.fixture
def global_tracer_mock(mocker):
    return mocker.patch("ariadne.contrib.tracing.opentracing.global_tracer")


@pytest.fixture
def active_span_mock(global_tracer_mock):
    return global_tracer_mock.return_value.start_active_span.return_value


def test_opentracing_extension_causes_no_errors_in_query_execution(schema):
    _, result = graphql(
        schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[OpenTracingExtension],
    )
    assert result == {"data": {"hello": "Hello, Bob!", "status": True}}


def test_opentracing_extension_uses_global_tracer(schema, global_tracer_mock):
    graphql(
        schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[OpenTracingExtension],
    )
    global_tracer_mock.assert_called_once()


def test_opentracing_extension_creates_span_for_query_root(schema, global_tracer_mock):
    graphql(schema, {"query": "{ status }"}, extensions=[OpenTracingExtension])
    global_tracer_mock.return_value.start_active_span.assert_any_call("GraphQL Query")


def test_opentracing_extension_creates_span_for_field(schema, global_tracer_mock):
    graphql(schema, {"query": "{ status }"}, extensions=[OpenTracingExtension])
    global_tracer_mock.return_value.start_active_span.assert_any_call("status")


def test_opentracing_extension_sets_graphql_component_tag_on_root_span(
    schema, active_span_mock
):
    graphql(
        schema,
        {"query": '{ status hello(name: "Bob") }'},
        extensions=[OpenTracingExtension],
    )
    active_span_mock.span.set_tag.assert_called_once_with(tags.COMPONENT, "graphql")


def test_opentracing_extension_calls_custom_arg_filter(schema, mocker):
    arg_filter = mocker.Mock(return_value={})
    graphql(
        schema,
        {"query": '{ hello(name: "Bob") }'},
        extensions=[opentracing_extension(arg_filter=arg_filter)],
    )
    arg_filter.assert_called_once_with({"name": "Bob"}, ANY)


def test_opentracing_extension_sets_filtered_args_on_span(
    schema, active_span_mock, mocker
):
    arg_filter = mocker.Mock(return_value={"name": "[filtered]"})
    graphql(
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


def test_opentracing_extension_handles_errors_in_resolvers(schema):
    _, result = graphql(
        schema, {"query": "{ testError status }"}, extensions=[OpenTracingExtension]
    )
    assert result["data"] == {"testError": None, "status": True}


def test_opentracing_extension_doesnt_break_introspection(schema):
    introspection_query = get_introspection_query(descriptions=True)
    _, result = graphql(
        schema, {"query": introspection_query}, extensions=[OpenTracingExtension]
    )
    assert "errors" not in result


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

    extension = OpenTracingExtension(arg_filter=arg_filter)
    test_file = MockFile("hello.txt", 2137)

    kwargs = {"0": test_file}
    info = mocker.Mock()

    copied_kwargs = extension.filter_resolver_args(kwargs, info)
    assert (
        "<class 'tests.tracing.test_opentracing_sync.MockFile'>"
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
            "<class 'tests.tracing.test_opentracing_sync.MockFile'>"
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
                    "<class 'tests.tracing.test_opentracing_sync.MockFile'>"
                    "(mime_type=not/available, size=37, filename=other.txt)"
                ),
            ],
        },
    } == result
