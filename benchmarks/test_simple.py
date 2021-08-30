from main import benchmark_simple, benchmark_simple_list


def test_benchmark_simple_query_post_return_list_of_500_elements(benchmark):
    simple_query_list = """
    {
      people{
        name,
        age
      }
    }
    """

    result = benchmark(benchmark_simple_list, query=simple_query_list)
    assert result == 200


def test_benchmark_simple_query_post_return_one_element(benchmark):
    simple_query = """
    {
      person{
        name,
        age
      }
    }
    """

    result = benchmark(benchmark_simple, query=simple_query)
    assert result == 200


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
    assert result == 400
