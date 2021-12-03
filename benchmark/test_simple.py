from starlette.testclient import TestClient

from ariadne.asgi import GraphQL

SIMPLE_QUERY = """
    {
        users {
            id
            name
        }
    }
"""


def test_benchmark_simple_query_resolved_to_one_dict(
    benchmark, schema, raw_data_one_item
):
    app = GraphQL(schema, root_value=raw_data_one_item)
    client = TestClient(app)

    def api_call():
        return client.post("/", json={"query": SIMPLE_QUERY})

    result = benchmark(api_call)
    assert result.status_code == 200


def test_benchmark_simple_query_resolved_to_500_dicts(benchmark, schema, raw_data):
    app = GraphQL(schema, root_value=raw_data)
    client = TestClient(app)

    def api_call():
        return client.post("/", json={"query": SIMPLE_QUERY})

    result = benchmark(api_call)
    assert result.status_code == 200


def test_benchmark_simple_query_resolved_to_one_object(
    benchmark, schema, hydrated_data_one_item
):
    app = GraphQL(schema, root_value={"users": hydrated_data_one_item})
    client = TestClient(app)

    def api_call():
        return client.post("/", json={"query": SIMPLE_QUERY})

    result = benchmark(api_call)
    assert result.status_code == 200


def test_benchmark_simple_query_resolved_to_500_objects(
    benchmark, schema, hydrated_data
):
    app = GraphQL(schema, root_value={"users": hydrated_data})
    client = TestClient(app)

    def api_call():
        return client.post("/", json={"query": SIMPLE_QUERY})

    result = benchmark(api_call)
    assert result.status_code == 200
