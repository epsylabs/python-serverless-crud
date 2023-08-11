import pytest

from serverless_crud.utils import identity
from test.utils import load_event


@pytest.mark.freeze_time("2022-01-19T23:07:25Z")
def test_identify():
    event = load_event("appsync/createDevice.json")
    assert identity(event, use_username=False) == "0b44ac7a-c793-4e4d-9b2d-0634be07598f"
    assert identity(event, use_username=True) == "michal"

    event = load_event("graphql/getDevice_cognito.json")
    assert identity(event, use_username=False) == "0b44ac7a-c793-4e4d-9b2d-0634be07598f"
    assert identity(event, use_username=True) == "michal"

    event = load_event("graphql/getDevice_iam.json")
    assert identity(event, use_username=False) == "0b44ac7a-c793-4e4d-9b2d-0634be07598f"
    assert identity(event, use_username=True) == "anon."  # No username/cognito:username with IAM

    event = load_event("rest/get.json")
    assert identity(event, use_username=False) == "0b44ac7a-c793-4e4d-9b2d-0634be07598f"
    assert identity(event, use_username=True) == "791791ac-b6c7-454e-89d0-927850869d06"
