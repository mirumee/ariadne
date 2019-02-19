from unittest.mock import Mock

from graphql import graphql_sync, build_schema

from ariadne import Interface, ResolverMap


type_defs = """
    type Query {
        cat: Cat!
        dog: Dog!
    }

    type Cat implements Sound {
        sound: String!
    }

    type Dog implements Sound {
        sound: String!
    }

    interface Sound {
        sound: String!
    }
"""

Cat = Mock(make_sound=Mock(return_value="Meow"))
Dog = Mock(make_sound=Mock(return_value="Bark"))


def test_interface_binds_its_resolvers_to_implementing_types_fields():
    schema = build_schema(type_defs)

    query = ResolverMap("Query")
    query.field("cat", resolver=lambda *_: Cat)
    query.field("dog", resolver=lambda *_: Dog)
    query.bind_to_schema(schema)

    def interface_resolver(obj, *_):
        return obj.make_sound()

    sound = Interface("Sound")
    sound.field("sound", resolver=interface_resolver)
    sound.bind_to_schema(schema)

    result = graphql_sync(schema, "{ cat { sound } dog { sound } }")

    assert result.data == {"cat": {"sound": "Meow"}, "dog": {"sound": "Bark"}}
