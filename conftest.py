import pytest

from serverless_crud import api
from serverless_crud.dynamodb import annotation as db
from serverless_crud.model import BaseModel


@pytest.fixture(autouse=True, scope="module")
def app():
    @db.Model(
        key=db.PrimaryKey(id=db.KeyFieldTypes.HASH),
        indexes=(db.GlobalSecondaryIndex("by_user", user=db.KeyFieldTypes.HASH, created=db.KeyFieldTypes.RANGE),),
        owner_field="user",
    )
    class Device(BaseModel):
        id: str
        created: int
        user: str = None

    api.rest.registry(Device, alias="device")
    api.appsync.registry(Device)

    return api
