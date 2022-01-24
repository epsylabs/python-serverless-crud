from test.utils import load_event


def test_creator(app):
    mock_event = load_event("appsync/createDevice.json")

    obj = app.appsync.handle(mock_event, {})

    assert obj.get("id") == mock_event.get("arguments").get("input").get("id")


def test_delete(app):
    mock_event = load_event("appsync/deleteDevice.json")

    obj = app.appsync.handle(mock_event, {})

    assert obj is None


def test_update(app):
    mock_event = load_event("appsync/updateDevice.json")

    obj = app.appsync.handle(mock_event, {})

    assert obj.get("create") == mock_event.get("arguments").get("input").get("create")
