from serverless_crud.utils import identity
from test.utils import load_event


def test_identify():
    event = load_event("appsync/createDevice.json")
    identity(event) == "xx"
