import hashlib
from functools import partial
from typing import Union

import pytest
from graphql import default_field_resolver, graphql_sync
from graphql.type import (
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLID,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLUnionType,
)

from ariadne import (
    ObjectType,
    QueryType,
    SchemaDirectiveVisitor,
    UnionType,
    make_executable_schema,
)


class UpperDirective(SchemaDirectiveVisitor):
    def visit_field_definition(
        self,
        field: GraphQLField,
        object_type: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> GraphQLField:
        original_resolver = field.resolve or default_field_resolver

        def resolve_upper(obj, info, **kwargs):
            result = original_resolver(obj, info, **kwargs)
            return result.upper()

        field.resolve = resolve_upper
        return field


class ReverseDirective(SchemaDirectiveVisitor):
    def visit_field_definition(
        self,
        field: GraphQLField,
        object_type: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> GraphQLField:
        original_resolver = field.resolve or default_field_resolver

        def resolve_reverse(obj, info, **kwargs):
            result = original_resolver(obj, info, **kwargs)
            return result[::-1]

        field.resolve = resolve_reverse
        return field


def test_field_definition_directive_replaces_field_resolver_with_custom_one():
    type_defs = """
        directive @upper on FIELD_DEFINITION
        directive @reverse on FIELD_DEFINITION

        type Query {
            test: Custom
        }

        type Custom {
            node: String @upper
            name: String @reverse
        }
    """

    query = QueryType()
    query.set_field("test", lambda *_: {"node": "custom", "name": "uppercase"})

    schema = make_executable_schema(
        type_defs,
        [query],
        directives={"upper": UpperDirective, "reverse": ReverseDirective},
    )

    result = graphql_sync(schema, "{ test { node name }}")
    assert result.errors is None
    assert result.data == {"test": {"node": "CUSTOM", "name": "esacreppu"}}


def test_multiple_field_definition_directives_replace_field_resolver_with_chainable_resolvers():  # noqa: E501
    type_defs = """
        directive @upper on FIELD_DEFINITION
        directive @reverse on FIELD_DEFINITION

        type Query {
            hello: String @upper @reverse
        }
    """

    query = QueryType()
    query.set_field("hello", lambda *_: "hello world")

    schema = make_executable_schema(
        type_defs,
        [query],
        directives={"upper": UpperDirective, "reverse": ReverseDirective},
    )

    result = graphql_sync(schema, "{ hello }")
    assert result.errors is None
    assert result.data == {"hello": "DLROW OLLEH"}


class ReturnValueDirective(SchemaDirectiveVisitor):
    def visit_field_definition(
        self,
        field: GraphQLField,
        object_type: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> GraphQLField:
        def resolver(*_):
            return self.args.get("arg")

        field.resolve = resolver
        return field


def test_directive_can_have_optional_argument():
    type_defs = """
        directive @test(arg: String) on FIELD_DEFINITION

        type Query {
            hello: String @test
        }
    """

    query = QueryType()
    query.set_field("hello", lambda *_: "hello world")

    schema = make_executable_schema(
        type_defs, [query], directives={"test": ReturnValueDirective}
    )

    result = graphql_sync(schema, "{ hello }")
    assert result.errors is None
    assert result.data == {"hello": None}


def test_directive_can_have_required_argument():
    type_defs = """
        directive @test(arg: String) on FIELD_DEFINITION

        type Query {
            hello: String @test(arg: "OK!")
        }
    """

    query = QueryType()
    query.set_field("hello", lambda *_: "hello world")

    schema = make_executable_schema(
        type_defs, [query], directives={"test": ReturnValueDirective}
    )

    result = graphql_sync(schema, "{ hello }")
    assert result.errors is None
    assert result.data == {"hello": "OK!"}


def test_directive_raises_type_error_if_required_argument_is_not_given():
    type_defs = """
        directive @test(arg: String!) on FIELD_DEFINITION

        type Query {
            hello: String @test
        }
    """

    with pytest.raises(TypeError):
        make_executable_schema(type_defs, directives={"test": ReturnValueDirective})


def test_directive_raises_type_error_if_there_is_typo():
    type_defs = """
        directive @test on FIELD_DEFINITION

        type Query {
            hello: String! @test,
        }
    """

    with pytest.raises(ValueError):
        make_executable_schema(
            type_defs, directives={"test_typo": ReturnValueDirective}
        )


def test_can_implement_unique_id_directive():
    type_defs = """
        directive @uniqueID(name: String, from: [String]) on OBJECT

        type Query {
            people: [Person]
            locations: [Location]
        }

        type Person @uniqueID(name: "uid", from: ["personID"]) {
            personID: Int
            name: String
        }

        type Location @uniqueID(name: "uid", from: ["locationID"]) {
            locationID: Int
            address: String
        }
    """

    class UniqueIDDirective(SchemaDirectiveVisitor):
        def visit_object(self, object_: GraphQLObjectType) -> GraphQLObjectType:
            name, from_ = self.args.values()

            def _field_resolver(field, _):
                hash_ = hashlib.sha1(object_.name.encode())
                for field_name in from_:
                    hash_.update(str(field[field_name]).encode())

                return hash_.hexdigest()

            object_.fields[name] = GraphQLField(
                description="Unique ID", type_=GraphQLID, resolve=_field_resolver
            )

    query = QueryType()
    query.set_field("people", lambda *_: [{"personID": 1, "name": "Ben"}])
    query.set_field(
        "locations", lambda *_: [{"locationID": 1, "address": "140 10th St"}]
    )
    schema = make_executable_schema(
        type_defs, [query], directives={"uniqueID": UniqueIDDirective}
    )

    result = graphql_sync(
        schema,
        """
        {
            people {
                uid
                personID
                name
            }
            locations {
                uid
                locationID
                address
            }
        }
        """,
    )
    assert result.errors is None
    assert result.data == {
        "locations": [
            {
                "uid": "c31b71e6e23a7ae527f94341da333590dd7cba96",
                "locationID": 1,
                "address": "140 10th St",
            }
        ],
        "people": [
            {
                "uid": "580a207c8e94f03b93a2b01217c3cc218490571a",
                "personID": 1,
                "name": "Ben",
            }
        ],
    }


def test_can_implement_remove_enum_values_directive():
    type_defs = """
        directive @remove(if: Boolean) on ENUM_VALUE

        type Query {
            age(unit: AgeUnit): Int
        }

        enum AgeUnit {
            DOG_YEARS
            TURTLE_YEARS @remove(if: true)
            PERSON_YEARS @remove(if: false)
        }
    """

    class RemoveEnumDirective(SchemaDirectiveVisitor):
        def visit_enum_value(self, value: GraphQLEnumValue, enum_type: GraphQLEnumType):
            if self.args["if"]:
                return False
            return None

    schema = make_executable_schema(
        type_defs, directives={"remove": RemoveEnumDirective}
    )

    enum_type: GraphQLEnumType = schema.get_type("AgeUnit")
    assert list(enum_type.values.keys()) == ["DOG_YEARS", "PERSON_YEARS"]


def test_can_swap_names_of_GraphQLNamedType_objects():  # noqa: N802
    class RenameTypeDirective(SchemaDirectiveVisitor):
        def visit_object(self, object_: GraphQLObjectType):
            object_.name = self.args["to"]

    type_defs = """
        directive @rename(to: String) on OBJECT

        type Query {
            people: [Person]
        }

        type Person @rename(to: "Human") {
            heightInInches: Int
        }

        scalar Date

        type Human @rename(to: "Person") {
            born: Date
        }
    """

    schema = make_executable_schema(
        type_defs, directives={"rename": RenameTypeDirective}
    )

    human = schema.get_type("Human")

    assert human.name == "Human"
    assert human.fields["heightInInches"].type == GraphQLInt

    person = schema.get_type("Person")
    assert person.name == "Person"
    assert person.fields["born"].type == schema.get_type("Date")

    query = schema.get_type("Query")
    people_type = query.fields["people"].type
    assert people_type.of_type == human


def test_defining_non_callable_visitor_attribute_raises_error():
    type_defs = """
        directive @schemaDirective on SCHEMA

        schema @schemaDirective {
            query: Query
        }

        type Query {
            people: [String]
        }
    """

    class Visitor(SchemaDirectiveVisitor):
        visit_schema = True

    with pytest.raises(ValueError):
        make_executable_schema(type_defs, directives={"schemaDirective": Visitor})


def test_returning_value_from_visit_schema_raises_error():
    type_defs = """
        directive @schemaDirective on SCHEMA

        schema @schemaDirective {
            query: Query
        }

        type Query {
            people: [String]
        }
    """

    class Visitor(SchemaDirectiveVisitor):
        def visit_schema(self, schema: GraphQLSchema):
            return schema

    with pytest.raises(ValueError):
        make_executable_schema(type_defs, directives={"schemaDirective": Visitor})


def test_visitor_missing_method_raises_error():
    type_defs = """
        directive @objectFieldDirective on FIELD_DEFINITION

        type Query {
            people: [String] @objectFieldDirective
        }
    """

    class Visitor(SchemaDirectiveVisitor):
        def visit_object(self, object_: GraphQLObjectType):
            return object_

    with pytest.raises(ValueError):
        make_executable_schema(type_defs, directives={"objectFieldDirective": Visitor})


def test_can_be_used_to_implement_auth_example():  # noqa: C901
    roles = ["UNKNOWN", "USER", "REVIEWER", "ADMIN"]

    class User:
        def __init__(self, token: str):
            self.token_index = roles.index(token)

        def has_role(self, role: str):
            role_index = roles.index(role)
            return self.token_index >= role_index >= 0

    def _get_user(token: str):
        return User(token)

    class AuthDirective(SchemaDirectiveVisitor):
        def visit_object(self, object_: GraphQLObjectType):
            self.ensure_fields_wrapped(object_)
            setattr(object_, "_required_auth_role", self.args["requires"])

        def visit_field_definition(
            self,
            field: GraphQLField,
            object_type: Union[GraphQLObjectType, GraphQLInterfaceType],
        ) -> GraphQLField:
            self.ensure_fields_wrapped(object_type)
            setattr(field, "_required_auth_role", self.args["requires"])

        def ensure_fields_wrapped(self, object_type: GraphQLObjectType):
            if hasattr(object_type, "_auth_fields_wrapped"):
                return
            setattr(object_type, "_auth_fields_wrapped", True)

            def _resolver(_, info, *, f=None, o=None):
                required_role = getattr(f, "_required_auth_role", None) or getattr(
                    o, "_required_auth_role", None
                )

                if not required_role:
                    return original_resolver(_, info)

                context = info.context

                user = _get_user(context["headers"]["authToken"])
                if not user.has_role(required_role):
                    raise ValueError("not authorized")

                return original_resolver(_, info)

            for _, field in object_type.fields.items():
                original_resolver = field.resolve or default_field_resolver
                field.resolve = partial(_resolver, f=field, o=object_type)

    type_defs = """
        directive @auth(
            requires: Role = ADMIN,
        ) on OBJECT | FIELD_DEFINITION

        enum Role {
            ADMIN
            REVIEWER
            USER
            UNKNOWN
        }

        type User @auth(requires: USER) {
            name: String
            banned: Boolean @auth(requires: ADMIN)
            canPost: Boolean @auth(requires: REVIEWER)
        }

        type Query {
            users: [User]
        }
    """

    query = QueryType()

    @query.field("users")
    def _users_resolver(_, __):
        return [{"banned": True, "canPost": False, "name": "Ben"}]

    schema = make_executable_schema(
        type_defs, [query], directives={"auth": AuthDirective}
    )

    def exec_with_role(role: str):
        return graphql_sync(
            schema,
            """
            query {
                users {
                    name
                    banned
                    canPost
                }
            }
            """,
            context_value={"headers": {"authToken": role}},
        )

    def _check_results(result, *, data=None, errors=None):
        if errors and result.errors:
            assert len(errors) == len(result.errors)
            for e in result.errors:
                assert e.message == "not authorized"
                assert e.path[-1] in errors

        assert result.data == data

    _check_results(
        exec_with_role("UNKNOWN"),
        data={"users": [{"name": None, "banned": None, "canPost": None}]},
        errors=("name", "banned", "canPost"),
    )
    _check_results(
        exec_with_role("USER"),
        data={"users": [{"name": "Ben", "banned": None, "canPost": None}]},
        errors=("banned", "canPost"),
    )
    _check_results(
        exec_with_role("REVIEWER"),
        data={"users": [{"name": "Ben", "banned": None, "canPost": False}]},
        errors=("banned",),
    )
    _check_results(
        exec_with_role("ADMIN"),
        data={"users": [{"name": "Ben", "banned": True, "canPost": False}]},
    )


def test_directive_can_add_new_type_to_schema():
    type_defs = """
        directive @key on OBJECT

        type Query {
            people: [String]
        }
        type User @key {
            id: Int
        }

        type Admin @key {
            id: Int
        }
    """

    class Visitor(SchemaDirectiveVisitor):
        def visit_object(self, object_: GraphQLObjectType):
            try:
                types = self.schema.type_map["_Entity"].types
            except KeyError:
                u = self.schema.type_map["_Entity"] = GraphQLUnionType("_Entity", [])
                types = u.types

            self.schema.type_map["_Entity"].types = types + (object_,)

    schema = make_executable_schema(type_defs, directives={"key": Visitor})
    assert {t.name for t in schema.get_type("_Entity").types} == {"User", "Admin"}


def test_directive_can_be_defined_without_being_used():
    type_defs = """
        directive @customdirective on OBJECT | INTERFACE

        union UnionTest = Type1 | Type2

        type Query {
            hello: String
        }

        type Type1 {
            foo: String
        }

        type Type2 {
            bar: String
        }
    """

    class CustomDirective(SchemaDirectiveVisitor):
        def visit_object(self, object_):
            pass

        def visit_interface(self, interface):
            pass

    type_1 = ObjectType("Type1")
    type_2 = ObjectType("Type2")

    def resolve_union_test_type(*_):
        return "AccessError"  # noop type resolver for test

    query = QueryType()
    union_test = UnionType("UnionTest", resolve_union_test_type)

    make_executable_schema(
        type_defs,
        [query, union_test, type_1, type_2],
        directives={"customdirective": CustomDirective},
    )
