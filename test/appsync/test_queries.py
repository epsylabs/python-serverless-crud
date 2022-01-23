from test.utils import load_event


def test_direct_resolver(app):
    mock_event = load_event("appsync/getDevice.json")

    result, obj = app.appsync.handle(mock_event, {})

    assert obj.id == "242942344"
