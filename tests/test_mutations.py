from ariadne import execute_query, make_executable_schema


def test_mutation_return_default_scalar():
    type_defs = """
        schema {
            query: Query
            mutation: Mutation
        }

        type Query {
            _: String
        }

        type Mutation {
            sum(a: Int, b: Int): Int
        }
    """

    resolvers = {"Mutation": {"sum": lambda *_, a, b: a + b}}

    schema = make_executable_schema(type_defs, resolvers)

    result = execute_query(schema, "mutation { sum(a: 1, b: 2) }")
    assert result.errors is None
    assert result.data == {"sum": 3}


def test_mutation_return_type():
    type_defs = """
        schema {
            query: Query
            mutation: Mutation
        }

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

    result = execute_query(schema, 'mutation { addStaff(name: "Bob") { name } }')
    assert result.errors is None
    assert result.data == {"addStaff": {"name": "Bob"}}
