from test.utils import load_event


def test_get_device(app):
    mock_event = load_event("appsync/getDevice.json")

    obj = app.appsync.handle(mock_event, {})

    assert obj.get("id") == "xxx-yyy-zzz"


def test_list_devices(app):
    mock_event = load_event("appsync/listDevices.json")

    obj = app.appsync.handle(mock_event, {})

    assert obj.get("id") == "xxx-yyy-zzz"
