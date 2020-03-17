import asyncio
from functools import wraps
from typing import Optional, Union, Callable, Dict, Any

from graphql import GraphQLError, parse


def convert_camel_case_to_snake(graphql_name: str) -> str:
    python_name = ""
    for i, c in enumerate(graphql_name.lower()):
        if i and c != graphql_name[i]:
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
    def convert_to_snake_case(d: Dict) -> Dict:
        converted: Dict = {}
        for k, v in d.items():
            if isinstance(v, dict):
                v = convert_to_snake_case(v)
            if isinstance(v, list):
                v = [convert_to_snake_case(i) if isinstance(i, dict) else i for i in v]
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
