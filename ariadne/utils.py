import asyncio
import inspect
from collections.abc import Mapping
from functools import wraps
from typing import Any, Callable, Optional, Union, cast
from warnings import warn

from graphql import GraphQLError, GraphQLNamedType, GraphQLType, parse
from graphql.language import DocumentNode, OperationDefinitionNode, OperationType


def convert_camel_case_to_snake(graphql_name: str) -> str:
    """Converts a string with `camelCase` name to `snake_case`.

    Utility function used by Ariadne's name conversion logic for mapping GraphQL
    names using the `camelCase` convention to Python counterparts in `snake_case`.

    Returns a string with converted name.

    # Required arguments

    `graphql_name`: a `str` with name to convert.

    # Example

    All characters in converted name are lowercased:

    ```python
    assert convert_camel_case_to_snake("URL") == "url"
    ```

    `_` is inserted before every uppercase character that's not first and is not
    preceded by other uppercase character:

    ```python
    assert convert_camel_case_to_snake("testURL") == "test_url"
    ```

    `_` is inserted before every uppercase character succeeded by lowercased
    character:

    ```python
    assert convert_camel_case_to_snake("URLTest") == "url_test"
    ```

    `_` is inserted before every digit that's not first and is not preceded by
    other digit:

    ```python
    assert convert_camel_case_to_snake("Rfc123") == "rfc_123"
    ```
    """

    max_index = len(graphql_name) - 1
    lowered_name = graphql_name.lower()

    python_name = ""
    for i, c in enumerate(lowered_name):
        if i > 0 and (
            # testWord -> test_word
            (
                c != graphql_name[i]
                and graphql_name[i - 1] != "_"
                and graphql_name[i - 1] == python_name[-1]
            )
            # TESTWord -> test_word
            or (
                i < max_index
                and graphql_name[i] != c
                and graphql_name[i + 1] == lowered_name[i + 1]
                and graphql_name[i + 1] != "_"
            )
            # test134 -> test_134
            or (c.isdigit() and not graphql_name[i - 1].isdigit())
            # 134test -> 134_test
            or (
                not c.isdigit()
                and graphql_name[i] != "_"
                and graphql_name[i - 1].isdigit()
            )
        ):
            python_name += "_"
        python_name += c
    return python_name


def gql(value: str) -> str:
    """Verifies that given string is a valid GraphQL.

    Provides definition time validation for GraphQL strings. Returns unmodified
    string. Some IDEs provide GraphQL syntax for highlighting those strings.


    # Examples

    Python string in this code snippet will use GraphQL's syntax highlighting when
    viewed in VSCode:

    ```python
    type_defs = gql(
        \"\"\"
        type Query {
            hello: String!
        }
        \"\"\"
    )
    ```

    This code will raise a GraphQL parsing error:

    ```python
    type_defs = gql(
        \"\"\"
        type Query {
            hello String!
        }
        \"\"\"
    )
    ```
    """
    parse(value)
    return value


def unwrap_graphql_error(
    error: Union[GraphQLError, Optional[Exception]],
) -> Optional[Exception]:
    """Recursively unwrap exception when its instance of GraphQLError.

    GraphQL query executor wraps exceptions in `GraphQLError` instances which
    contain information about exception's origin in GraphQL query or it's result.

    Original exception is available through `GraphQLError`'s `original_error`
    attribute, but sometimes `GraphQLError` can be wrapped in other `GraphQLError`.

    Returns unwrapped exception or `None` if no original exception was found.

    # Example

    Below code unwraps original `KeyError` from multiple `GraphQLError` instances:

    ```python
    error = KeyError("I am a test!")

    assert (
        unwrap_graphql_error(
            GraphQLError(
                "Error 1", GraphQLError("Error 2", GraphQLError("Error 3", original_error=error))
            )
        )
        == error
    )
    ```

    Passing other exception to `unwrap_graphql_error` results in same exception
    being returned:

    ```python
    error = ValueError("I am a test!")
    assert unwrap_graphql_error(error) == error
    ```
    """  # noqa: E501

    if isinstance(error, GraphQLError):
        return unwrap_graphql_error(error.original_error)
    return error


def convert_kwargs_to_snake_case(func: Callable) -> Callable:
    """Decorator for resolvers recursively converting their kwargs to `snake_case`.

    Converts keys in `kwargs` dict from `camelCase` to `snake_case` using the
    `convert_camel_case_to_snake` function. Walks values recursively, applying
    same conversion to keys of nested dicts and dicts in lists of elements.

    Returns decorated resolver function.

    > **Deprecated:** This decorator is deprecated and will be deleted in future
    version of Ariadne. Set `out_name`s explicitly in your GraphQL schema or use
    the `convert_schema_names` option on `make_executable_schema`.
    """

    def convert_to_snake_case(m: Mapping) -> dict:
        converted: dict = {}
        for k, v in m.items():
            if isinstance(v, Mapping):
                v = convert_to_snake_case(v)
            if isinstance(v, list):
                v = [
                    convert_to_snake_case(i) if isinstance(i, Mapping) else i for i in v
                ]
            converted[convert_camel_case_to_snake(k)] = v
        return converted

    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **convert_to_snake_case(kwargs))

        return async_wrapper

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **convert_to_snake_case(kwargs))

    return wrapper


def type_implements_interface(interface: str, graphql_type: GraphQLType) -> bool:
    """Test if type definition from GraphQL schema implements an interface.

    Returns `True` if type implements interface and `False` if it doesn't.

    # Required arguments

    `interface`: a `str` with name of interface in GraphQL schema.

    `graphql_type`: a `GraphQLType` interface to test. It may or may not have
    the `interfaces` attribute.
    """

    try:
        return interface in [i.name for i in graphql_type.interfaces]  # type: ignore
    except AttributeError:
        pass

    return False


def get_operation_type(
    graphql_document: DocumentNode, operation_name: Optional[str] = None
) -> OperationType:
    if operation_name:
        for d in graphql_document.definitions:
            d = cast(OperationDefinitionNode, d)
            if d.name and d.name.value == operation_name:
                return d.operation
    else:
        for definition in graphql_document.definitions:
            if isinstance(definition, OperationDefinitionNode):
                return definition.operation
    raise RuntimeError("Can't get GraphQL operation type")


def context_value_one_arg_deprecated():  # TODO: remove in 0.20
    warn(
        "'context_value(request)' has been deprecated and will raise a type "
        "error in Ariadne 0.20. Change definition to "
        "'context_value(request, data)'.",
        DeprecationWarning,
        stacklevel=2,
    )


def type_set_extension(
    object_type: GraphQLNamedType, extension_name: str, value: Any
) -> None:
    if getattr(object_type, "extensions", None) is None:
        object_type.extensions = {}
    object_type.extensions[extension_name] = value


def type_get_extension(
    object_type: GraphQLNamedType, extension_name: str, fallback: Any = None
) -> Any:
    return getattr(object_type, "extensions", {}).get(extension_name, fallback)


def is_async_callable(obj: Any) -> bool:
    return inspect.iscoroutinefunction(obj) or (
        callable(obj) and inspect.iscoroutinefunction(obj.__call__)
    )
