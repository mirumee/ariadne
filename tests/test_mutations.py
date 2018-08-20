from graphql import graphql

from ariadne import make_executable_schema


def test_mutation_return_default_scalar():
    type_defs = """
        type Query {
            _: String
        }

        type Mutation {
            sum(a: Int, b: Int): Int
        }
    """

    resolvers = {"Mutation": {"sum": lambda *_, a, b: a + b}}

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "mutation { sum(a: 1, b: 2) }")
    assert result.errors is None
    assert result.data == {"sum": 3}


def test_mutation_return_type():
    type_defs = """
        type Query {
            _: String
        }

        type Staff {
            name: String
        }

        type Mutation {
            addStaff(name: String): Staff
        }
    """

    def resolve_add_staff(*_, name):
        assert name == "Bob"
        return {"name": name}

    resolvers = {"Mutation": {"addStaff": resolve_add_staff}}

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, 'mutation { addStaff(name: "Bob") { name } }')
    assert result.errors is None
    assert result.data == {"addStaff": {"name": "Bob"}}


def test_mutation_input():
    type_defs = """
        type Query {
            _: String
        }

        input StaffInput {
            name: String
        }

        type Staff {
            name: String
        }

        type Mutation {
            addStaff(data: StaffInput): Staff
        }
    """

    def resolve_add_staff(*_, data):
        assert data == {"name": "Bob"}
        return data

    resolvers = {"Mutation": {"addStaff": resolve_add_staff}}

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, 'mutation { addStaff(data: { name: "Bob" }) { name } }')
    assert result.errors is None
    assert result.data == {"addStaff": {"name": "Bob"}}
