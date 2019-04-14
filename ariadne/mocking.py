import random
from functools import partial
from inspect import isawaitable
from typing import Any

from ariadne import FallbackResolversSetter
from graphql.type import (
    GraphQLEnumType,
    GraphQLField,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLResolveInfo,
    GraphQLScalarType,
    GraphQLUnionType,
    ResponsePath,
)


def generate_scalar(value, path, of_type):
    if of_type.name == "Boolean":
        return random.choice([True, False])
    if of_type.name == "Float":
        return random.random()
    if of_type.name == "ID":
        return str(path)
    if of_type.name == "Int":
        return random.randint(0, 100)
    if of_type.name == "String":
        return str(path)
    return None


async def maybe_wrap_object(value, of_type):
    if isawaitable(value):
        value = await value
    if isinstance(value, dict):
        value["__typename"] = of_type.name
    return value


def generate_value(
    value, of_type: GraphQLOutputType, *, factory_map: dict, path, **kwargs
):
    if isinstance(of_type, GraphQLNonNull):
        of_type = of_type.of_type
    if isinstance(of_type, GraphQLList):
        if value is None:
            value = [
                generate_value(
                    value, of_type.of_type, factory_map=factory_map, path=path, **kwargs
                )
            ]
    if isinstance(of_type, GraphQLObjectType):
        factory = factory_map.get(of_type.name, lambda _, **kwargs: {})
        value = factory(value, **kwargs)
        value = maybe_wrap_object(value, of_type)
    if isinstance(of_type, GraphQLEnumType):
        factory = factory_map.get(
            of_type.name, lambda _, **kwargs: random.choice(list(of_type.values.keys()))
        )
        value = factory(value, **kwargs)
    if isinstance(of_type, GraphQLScalarType):
        factory = factory_map.get(
            of_type.name, lambda value, **kwargs: generate_scalar(value, path, of_type)
        )
        value = factory(value, **kwargs)
    if isinstance(of_type, GraphQLUnionType):
        factory = factory_map.get(
            of_type.name,
            lambda value, **kwargs: generate_value(
                value,
                random.choice(of_type.types),
                factory_map=factory_map,
                path=path,
                **kwargs,
            ),
        )
        value = factory(value, **kwargs)
    return value


def build_id(path: ResponsePath):
    elements = []
    while path:
        elements.append(str(path.key))
        path = path.prev
    return ".".join(elements[::-1])


def mock_resolver(
    parent: Any, info: GraphQLResolveInfo, *, factory_map: dict, **kwargs
):
    name = info.field_name
    value = None
    if isinstance(parent, dict) and name in parent:
        value = parent.get(name)
    elif hasattr(parent, name):
        value = getattr(parent, name)
    return generate_value(
        value,
        of_type=info.return_type,
        factory_map=factory_map,
        path=build_id(info.path),
        **kwargs,
    )


class FactoryMap(dict):
    def type(self, name):
        def decorator(fun):
            self[name] = fun
            return fun

        return decorator


class MockResolverSetter(FallbackResolversSetter):
    def __init__(self, factory_map=None):
        self.resolver = partial(mock_resolver, factory_map=factory_map)
        super().__init__()

    def add_resolver_to_field(self, _: str, field_object: GraphQLField) -> None:
        if field_object.resolve is None:
            field_object.resolve = self.resolver
