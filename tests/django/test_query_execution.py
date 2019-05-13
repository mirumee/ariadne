from ariadne.contrib.django.views import GraphQLView


def test_post_request_fails_if_request_content_type_is_not_json(
    schema, request_factory, snapshot
):
    view = GraphQLView.as_view(schema=schema)
    request = request_factory.post("/graphql/", content_type="text/plain")
    response = view(request)
    assert response.status_code == 400
    snapshot.assert_match(response.content)


def test_post_request_fails_if_request_data_is_malformed_json(
    schema, request_factory, snapshot
):
    view = GraphQLView.as_view(schema=schema)
    request = request_factory.post(
        "/graphql/", data="{malformed", content_type="application/json"
    )
    response = view(request)
    assert response.status_code == 400
    snapshot.assert_match(response.content)


def test_query_in_valid_post_request_is_executed(schema, request_factory, snapshot):
    view = GraphQLView.as_view(schema=schema)
    request = request_factory.post(
        "/graphql/", data={"query": "{ status }"}, content_type="application/json"
    )
    response = view(request)
    assert response.status_code == 200
    snapshot.assert_match(response.content)
