from troposphere.dynamodb import AttributeDefinition, KeySchema, Projection, GlobalSecondaryIndex
from troposphere.dynamodb import (
    LocalSecondaryIndex as AWSLocalSecondaryIndex,
    GlobalSecondaryIndex as AWSGlobalSecondaryIndex,
    ProvisionedThroughput as AWSProvisionedThroughput,
)

from serverless_crud.dynamodb.annotation import DynamoIndex, DynamodbMetadata, LocalSecondaryIndex, GlobalSecondaryIndex
from serverless_crud.model import BaseModel

PYTHON_TO_DYNAMODB = {
    int: "N",
    complex: "N",
    float: "N",
    memoryview: "B",
    bytearray: "B",
    bytes: "B",
}


def create_index(index: DynamoIndex):
    index_dict = dict(
        IndexName=index.name,
        KeySchema=[KeySchema(AttributeName=name, KeyType=str(type_)) for name, type_ in index.fields.items()],
        Projection=Projection(ProjectionType=str(index.projection), NonKeyAttributes=index.non_key_attributes),
    )

    if isinstance(index, GlobalSecondaryIndex) and index.throughput:
        throughput = {}
        if index.throughput.read:
            throughput["ReadCapacityUnits"] = index.throughput.read

        if index.throughput.write:
            throughput["WriteCapacityUnits"] = index.throughput.write

        index_dict["ProvisionedThroughput"] = AWSProvisionedThroughput()

    return index_dict


def model_to_table_specification(model: BaseModel):
    meta: DynamodbMetadata = model._meta
    dynamo_attributes = {k: PYTHON_TO_DYNAMODB.get(v.type_, "S") for k, v in model.__fields__.items()}

    billingMode = (
        "PROVISIONED"
        if len([i for i in meta.indexes if type(i) == GlobalSecondaryIndex and i.throughput])
        else "PAY_PER_REQUEST"
    )

    key_attributes = set(meta.key.key_fields.keys())

    for index in meta.indexes:
        key_attributes.update(set(index.fields.keys()))

    return dict(
        TableName=meta.table_name,
        BillingMode=billingMode,
        AttributeDefinitions=[
            AttributeDefinition(AttributeName=name, AttributeType=dynamo_attributes.get(name, "S"))
            for name in key_attributes
        ],
        KeySchema=[KeySchema(AttributeName=name, KeyType=str(type_)) for name, type_ in meta.key.key_fields.items()],
        GlobalSecondaryIndexes=[
            AWSGlobalSecondaryIndex(**create_index(index))
            for index in meta.indexes
            if isinstance(index, GlobalSecondaryIndex)
        ],
        LocalSecondaryIndexes=[
            AWSLocalSecondaryIndex(**create_index(index))
            for index in meta.indexes
            if isinstance(index, LocalSecondaryIndex)
        ],
    )
