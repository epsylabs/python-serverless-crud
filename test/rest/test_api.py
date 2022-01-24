import json

from test.utils import load_event


def test_create_devices(app):
    mock_event = load_event("rest/create.json")
    body = json.loads(mock_event.get("body"))

    response = app.rest.handle(mock_event, {})
    response_body = json.loads(response.get("body"))

    assert response_body["id"] == body["id"]

