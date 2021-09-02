from starlette.testclient import TestClient
from ariadne.asgi import GraphQL


def test_benchmark_complex_query_post_return_list_of_500_elements(
    benchmark, complex_query_list, complex_data_from_json, schema
):
    app = GraphQL(schema, root_value=complex_data_from_json)
    client = TestClient(app)

    def wrapper():
        request = client.post("/", json={"query": complex_query_list})
        return request

    result = benchmark(wrapper)

    assert result.status_code == 200
