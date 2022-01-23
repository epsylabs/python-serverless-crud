from test.utils import load_event


def test_creator(app):
    mock_event = load_event("appsync/createDevice.json")

    result, obj = app.appsync.handle(mock_event, {})

    assert obj.id == "242942344"
