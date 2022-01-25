from moto import mock_dynamodb2
import boto3


def dothis():
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("Device")

    response = table.get_item(TableName="Device", Key={"id": "xxx-yyy-zzz1"})

    print(response)

    # item = table.get_item(Key=dict(id="xxx-yyy-zzz1"))
    # print(item)


@mock_dynamodb2
def test_moto():
    dynamodb = boto3.resource("dynamodb")

    table = dynamodb.create_table(
        TableName="Device",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    table = dynamodb.Table("Device")
    table.put_item(
        Item={"id": "xxx-yyy-zzz1", "created": 1234567889, "user": "5b9b13f1-dd60-43e4-a986-ea2a0e2ee90a"},
    )

    dothis()
