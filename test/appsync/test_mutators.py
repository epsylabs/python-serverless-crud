from test.utils import load_event


def test_creator(app):
    mock_event = load_event("appsync/createDevice.json")

    obj = app.appsync.handle(mock_event, {})

    assert obj.get("id") == mock_event.get("arguments").get("input").get("id")
