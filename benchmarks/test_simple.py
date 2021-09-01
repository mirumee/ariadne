import json
from main import benchmark_simple, benchmark_simple_list


def test_benchmark_simple_query_post_return_list_of_500_elements(benchmark):
    expected_number_of_elements = 500
    simple_query_list = """
    {
      people{
        name,
        age
      }
    }
    """

    result = benchmark(benchmark_simple_list, query=simple_query_list)
    items = json.loads(result.text)

    assert len(items["data"]["people"]) == expected_number_of_elements
    assert result.status_code == 200


def test_benchmark_simple_query_post_return_one_element(benchmark):
    expected_number_of_elements = 1
    simple_query = """
    {
      person{
        name,
        age
      }
    }
    """

    result = benchmark(benchmark_simple, query=simple_query)
    items = json.loads(result.text)

    assert len(items["data"]["person"]) == expected_number_of_elements
    assert result.status_code == 200


def test_benchmark_simple_with_bad_query_return_bad_request(benchmark):
    simple_query = """
    {
      person{
        namee,
        age
      }
    }
    """

    result = benchmark(benchmark_simple, query=simple_query)

    assert result.status_code == 400
