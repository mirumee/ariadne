import json

from main import benchmark_complex, benchmark_complex_list


def test_benchmark_complex_query_post_return_list_of_500_elements(benchmark):
    expected_number_of_elements = 500
    complex_query = """
    {
        users{
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

    result = benchmark(benchmark_complex_list, query=complex_query)
    items = json.loads(result.text)
    assert len(items["data"]["users"]) == expected_number_of_elements
    assert result.status_code == 200


def test_benchmark_complex_query_post_return_one_element(benchmark):
    expected_number_of_elements = 1
    complex_query = """
    {
        user{
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

    result = benchmark(benchmark_complex, query=complex_query)
    items = json.loads(result.text)
    assert len(items["data"]["user"]) == expected_number_of_elements
    assert result.status_code == 200


def test_benchmark_complex_query_post_return_bad_request(benchmark):
    complex_query = """
    {
        baduser{
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

    result = benchmark(benchmark_complex, query=complex_query)
    assert result.status_code == 400
