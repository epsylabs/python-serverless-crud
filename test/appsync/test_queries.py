from test.utils import load_event


def test_get_device(app):
    mock_event = load_event("appsync/getDevice.json")

    result = app.appsync.handle(mock_event, {})

    assert result.id == "xxx-yyy-zzz"


def test_list_devices(app):
    mock_event = load_event("appsync/listDevices.json")

    result = app.appsync.handle(mock_event, {})

    assert len(result) == 1
    assert result[0].id == "xxx-yyy-zzz"
