import boto3
import pytest
from moto.dynamodb2 import mock_dynamodb2

from serverless_crud import Manager
from serverless_crud.dynamodb import annotation as db
from serverless_crud.model import BaseModel


@db.Model(
    key=db.PrimaryKey(id=db.KeyFieldTypes.HASH),
    indexes=(db.GlobalSecondaryIndex("by_user", user=db.KeyFieldTypes.HASH, created=db.KeyFieldTypes.RANGE),),
    owner_field="user",
)
class Device(BaseModel):
    id: str
    created: int
    user: str = None


@pytest.fixture(autouse=True, scope="function")
def dynamo():
    with mock_dynamodb2():
        dynamo = boto3.resource("dynamodb")
        dynamo.create_table(
            TableName="Device",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}, {"AttributeName": "user", "AttributeType": "S"}],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'by_user',
                    'KeySchema': [
                        {
                            'AttributeName': 'user',
                            'KeyType': 'HASH'
                        },
                    ],
                    "Projection": {
                        "ProjectionType": "ALL"
                    }
                },
            ]
        )

        table = dynamo.Table("Device")
        table.put_item(
            Item={"id": "xxx-yyy-zzz", "created": 1234567889, "user": "0b44ac7a-c793-4e4d-9b2d-0634be07598f"},
        )

        yield dynamo


@pytest.fixture(scope="function")
def app():
    api = Manager()

    api.rest.registry(Device, alias="device")
    api.appsync.registry(Device)

    return api
