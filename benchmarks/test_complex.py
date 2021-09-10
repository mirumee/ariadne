from starlette.testclient import TestClient

from ariadne.asgi import GraphQL


def test_benchmark_complex_query_post_return_list_of_500_elements(
    benchmark, complex_query, complex_data_from_json, schema
):
    app = GraphQL(schema, root_value=complex_data_from_json)
    client = TestClient(app)

    def wrapper():
        request = client.post("/", json={"query": complex_query("users")})
        return request

    result = benchmark(wrapper)

    assert result.status_code == 200


def test_benchmark_complex_query_post_return_one_element(
    benchmark, complex_query, schema
):
    app = GraphQL(schema)
    client = TestClient(app)

    def wrapper():
        request = client.post("/", json={"query": complex_query("user")})
        return request

    result = benchmark(wrapper)

    assert result.status_code == 200


def test_benchmark_complex_query_post_return_list_500_dataclass(
    benchmark, complex_query, schema
):
    app = GraphQL(schema)
    client = TestClient(app)

    def wrapper():
        request = client.post("/", json={"query": complex_query("users_dataclass")})
        return request

    result = benchmark(wrapper)

    assert result.status_code == 200


def test_benchmark_complex_query_post_return_dataclass(
    benchmark, complex_query, schema
):
    app = GraphQL(schema)
    client = TestClient(app)

    def wrapper():
        request = client.post("/", json={"query": complex_query("user_dataclass")})
        return request

    result = benchmark(wrapper)

    assert result.status_code == 200
