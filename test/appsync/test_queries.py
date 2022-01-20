from test.utils import load_event


def test_direct_resolver(app):
    # Check whether we can handle an example appsync direct resolver
    # load_event primarily deserialize the JSON event into a dict
    mock_event = load_event("appsync/getDevice.json")

    result = app.appsync.handle(mock_event, {})

    assert result == "my identifier"
