from starlette.testclient import TestClient
from ariadne.asgi import GraphQL


def test_benchmark_simple_query_post_return_list_of_500_elements(
    benchmark, schema, simple_data_from_json, simple_query_list
):
    app = GraphQL(schema, root_value=simple_data_from_json)
    client = TestClient(app)

    def wrapper():
        request = client.post("/", json={"query": simple_query_list})
        return request

    result = benchmark(wrapper)

    assert result.status_code == 200


def test_benchmark_simple_query_post_return_one_element(
    benchmark, schema, simple_query
):
    app = GraphQL(schema)
    client = TestClient(app)

    def wrapper():
        request = client.post("/", json={"query": simple_query})
        return request

    result = benchmark(wrapper)
    assert result.status_code == 200
