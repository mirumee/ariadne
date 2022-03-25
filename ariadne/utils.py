import asyncio
from collections.abc import Mapping
from functools import wraps
from typing import Optional, Union, Callable, Dict, Any

from graphql import GraphQLError, GraphQLType, parse


def convert_camel_case_to_snake(graphql_name: str) -> str:
    # pylint: disable=too-many-boolean-expressions
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
                and graphql_name[i] != lowered_name[i]
                and graphql_name[i + 1] == lowered_name[i + 1]
            )
            # test134 -> test_134
            or (c.isdigit() and not graphql_name[i - 1].isdigit())
            # 134test -> 134_test
            or (not c.isdigit() and graphql_name[i - 1].isdigit())
        ):
            python_name += "_"
        python_name += c
    return python_name


def gql(value: str) -> str:
    parse(value)
    return value


def unwrap_graphql_error(
    error: Union[GraphQLError, Optional[Exception]]
) -> Optional[Exception]:
    if isinstance(error, GraphQLError):
        return unwrap_graphql_error(error.original_error)
    return error


def convert_kwargs_to_snake_case(func: Callable) -> Callable:
    def convert_to_snake_case(m: Mapping) -> Dict:
        converted: Dict = {}
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
    try:
        return interface in [i.name for i in graphql_type.interfaces]  # type: ignore
    except AttributeError:
        pass

    return False
