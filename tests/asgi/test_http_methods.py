def test_unsupported_patch(client):
    response = client.patch("/", json={})
    assert response.status_code == 405


def test_unsupported_put(client):
    response = client.patch("/", json={})
    assert response.status_code == 405
