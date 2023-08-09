import pytest

from serverless_crud.exceptions import EntityNotFoundException
from test.utils import load_event


def test_get_device(app):
    mock_event = load_event("appsync/getDevice.json")

    result = app.appsync.handle(mock_event, {})

    assert result.get("id") == "xxx-yyy-zzz"


def test_get_missing_device(app):
    mock_event = load_event("appsync/getMissingDevice.json")

    with pytest.raises(EntityNotFoundException):
        result = app.appsync.handle(mock_event, {})


def test_list_devices(app):
    mock_event = load_event("appsync/listDevice.json")

    result = app.appsync.handle(mock_event, {})

    assert len(result.get("items")) == 1
    assert result.get("items")[0].get("id") == "xxx-yyy-zzz"
