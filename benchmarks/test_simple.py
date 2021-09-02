from starlette.testclient import TestClient
from ariadne.asgi import GraphQL


def test_benchmark_simple_query_post_return_list_of_500_elements(
    benchmark, simple_query_list, simple_data_from_json, schema
):
    app = GraphQL(schema, root_value=simple_data_from_json)
    client = TestClient(app)

    def wrapper():
        request = client.post("/", json={"query": simple_query_list})
        return request

    result = benchmark(wrapper)
    print(result.text)
    assert result.status_code == 200
