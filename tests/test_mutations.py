from graphql import graphql_sync

from ariadne import MutationType, make_executable_schema


def test_executing_mutation_takes_scalar_args_and_returns_scalar_sum():
    type_defs = """
        type Query {
            _: String
        }

        type Mutation {
            sum(a: Int, b: Int): Int
        }
    """

    mutation = MutationType()
    mutation.set_field("sum", lambda *_, a, b: a + b)

    schema = make_executable_schema(type_defs, mutation)

    result = graphql_sync(schema, "mutation { sum(a: 1, b: 2) }")
    assert result.errors is None
    assert result.data == {"sum": 3}


def test_executing_mutation_takes_scalar_arg_and_returns_type():
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

    mutation = MutationType()

    @mutation.field("addStaff")
    def resolve_add_staff(*_, name):
        assert name == "Bob"
        return {"name": name}

    schema = make_executable_schema(type_defs, mutation)

    result = graphql_sync(schema, 'mutation { addStaff(name: "Bob") { name } }')
    assert result.errors is None
    assert result.data == {"addStaff": {"name": "Bob"}}


def test_executing_mutation_using_input_type():
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

    mutation = MutationType()

    @mutation.field("addStaff")
    def resolve_add_staff(*_, data):
        assert data == {"name": "Bob"}
        return data

    schema = make_executable_schema(type_defs, mutation)

    result = graphql_sync(
        schema, 'mutation { addStaff(data: { name: "Bob" }) { name } }'
    )
    assert result.errors is None
    assert result.data == {"addStaff": {"name": "Bob"}}
