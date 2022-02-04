import json

from test.utils import load_event


def test_create_devices(app):
    mock_event = load_event("rest/create.json")
    body = json.loads(mock_event.get("body"))

    response = app.rest.handle(mock_event, {})
    response_body = json.loads(response.get("body"))

    assert response_body["id"] == body["id"]


def test_get_device(app):
    mock_event = load_event("rest/get.json")

    response = app.rest.handle(mock_event, {})
    response_body = json.loads(response.get("body"))

    assert response_body["id"] == "xxx-yyy-zzz"


def test_update_device(app):
    mock_event = load_event("rest/update.json")

    response = app.rest.handle(mock_event, {})
    response_body = json.loads(response.get("body"))

    assert response_body["created"] == 234234500000


def test_delete_device(app):
    mock_event = load_event("rest/delete.json")

    response = app.rest.handle(mock_event, {})
    response_body = json.loads(response.get("body"))

    assert response_body == {}


def test_list_devices(app):
    mock_event = load_event("rest/search_index.json")

    response = app.rest.handle(mock_event, {})
    response_body = json.loads(response.get("body"))

    assert len(response_body["items"]) == 1
    assert response_body["items"][0]["id"] == "xxx-yyy-zzz"
