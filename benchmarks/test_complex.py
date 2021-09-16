from starlette.testclient import TestClient

from ariadne.asgi import GraphQL


def test_benchmark_complex_query_post_return_list_of_500_elements(
    benchmark, schema, raw_data
):
    app = GraphQL(schema, root_value=raw_data)

    client = TestClient(app)
    query = """
        {
            users{
                id
                name
                group{
                    name
                    roles
                }
                avatar{
                    size
                    url
                }
            }
        }
        """

    def wrapper():
        return client.post("/", json={"query": query})

    result = benchmark(wrapper)

    assert result.status_code == 200


def test_benchmark_complex_query_post_return_one_element(
    benchmark, schema, raw_data_one_element
):
    app = GraphQL(schema, root_value=raw_data_one_element)

    client = TestClient(app)
    query = """
        {
            users{
                id
                name
                group{
                    name
                    roles
                }
                avatar{
                    size
                    url
                }
            }
        }
        """

    def wrapper():
        return client.post("/", json={"query": query})

    result = benchmark(wrapper)

    assert result.status_code == 200


def test_benchmark_complex_query_post_return_list_500_dataclass(
    benchmark, schema, hydrated_data
):
    app = GraphQL(schema, root_value={"users": hydrated_data})

    client = TestClient(app)
    query = """
        {
            users{
                id
                name
                group{
                    name
                    roles
                }
                avatar{
                    size
                    url
                }
            }
        }
        """

    def wrapper():
        return client.post("/", json={"query": query})

    result = benchmark(wrapper)

    assert result.status_code == 200


def test_benchmark_complex_query_post_return_dataclass(
    benchmark, schema, hydrated_data_one_element
):
    app = GraphQL(schema, root_value={"users": hydrated_data_one_element})
    client = TestClient(app)
    query = """
        {
            users{
                id
                name
                group{
                    name
                    roles
                }
                avatar{
                    size
                    url
                }
            }
        }
        """

    def wrapper():
        return client.post("/", json={"query": query})

    result = benchmark(wrapper)

    assert result.status_code == 200
