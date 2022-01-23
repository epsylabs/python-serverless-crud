import boto3
import pytest
from moto import mock_dynamodb2

from serverless_crud import api
from serverless_crud.dynamodb import annotation as db
from serverless_crud.model import BaseModel


@pytest.fixture(autouse=True, scope="module")
@mock_dynamodb2
def app():
    dynamodb = boto3.resource('dynamodb')
    dynamodb.create_table(
        TableName='Device',
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ]
    )

    table = dynamodb.Table("Device")
    table.put_item(
        Item={
            "id": "xxx-yyy-zzz",
            "created": 1234567889,
            "user": "5b9b13f1-dd60-43e4-a986-ea2a0e2ee90a"
        },
    )

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
