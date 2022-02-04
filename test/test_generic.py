from serverless_crud.utils import identity
from test.utils import load_event


def test_identify():
    event = load_event("appsync/createDevice.json")
    assert identity(event) == "0b44ac7a-c793-4e4d-9b2d-0634be07598f"

    event = load_event("graphql/getDevice_cognito.json")
    assert identity(event) == "0b44ac7a-c793-4e4d-9b2d-0634be07598f"

    event = load_event("graphql/getDevice_iam.json")
    assert identity(event) == "0b44ac7a-c793-4e4d-9b2d-0634be07598f"

    event = load_event("rest/get.json")
    assert identity(event) == "0b44ac7a-c793-4e4d-9b2d-0634be07598f"
