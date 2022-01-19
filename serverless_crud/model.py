from enum import Enum
from typing import List

from aws_lambda_powertools.utilities.parser import BaseModel as ParserBaseModel
from boto3.dynamodb.conditions import Key


class KeyFieldTypes(Enum):
    HASH = "HASH"
    RANGE = "RANGE"

    def __str__(self):
        return self.value


class Projection(Enum):
    ALL = "ALL"
    KEYS_ONLY = "KEYS_ONLY"
    INCLUDE = "INCLUDE"

    def __str__(self):
        return self.value


class PrimaryKey:
    def __init__(self, **key_fields):
        self.key_fields = key_fields
        names = list(key_fields.keys())
        self.range_key = names.pop()
        self.hash_key = names.pop()
        self.partition_key = self.hash_key
        self.sort_key = self.range_key

    def append_condition_expression(self, query: dict, require="attribute_not_exists"):
        query["ConditionExpression"] = f"{require}(#partition_key)"
        query["ExpressionAttributeNames"] = {"#partition_key": self.partition_key}

        return query

    def append_key_expression(self, query: dict):
        query["KeyConditionExpression"] = Key()
        query["ExpressionAttributeNames"] = {"#partition_key": self.partition_key}

        return query


class DynamoIndex:
    def __init__(self, name, projection=Projection.KEYS_ONLY, non_key_attributes=None, **fields):
        self.name = name
        self.fields = fields
        self.projection = projection
        self.non_key_attributes = non_key_attributes or []


class LocalSecondaryIndex(DynamoIndex):
    def __init__(self, name, projection=Projection.KEYS_ONLY, non_key_attributes=None, **fields):
        super().__init__(name, projection, non_key_attributes, **fields)


class ProvisionedThroughput:
    def __init__(self, read=None, write=None):
        self.read = read
        self.write = write


class GlobalSecondaryIndex(LocalSecondaryIndex):
    def __init__(self, name, projection=Projection.KEYS_ONLY, non_key_attributes=None, throughput=None, **fields):
        super().__init__(name, projection, non_key_attributes, **fields)
        self.throughput = throughput


class DynamodbMetadata:
    def __init__(self, key: PrimaryKey, indexes: List[DynamoIndex], table_name=None, owner_field=None):
        self.key = key
        self.indexes = indexes or []
        self.table_name = table_name
        self.owner_field = owner_field

    def get_index(self, name) -> DynamoIndex:
        for idx in self.indexes:
            if idx.name == name:
                return idx


class BaseModel(ParserBaseModel):
    _meta: DynamodbMetadata = None

    def _field_type(self, field):
        return self.__fields__.get(field).type

    def get_primary_key(self):
        return {f: getattr(self, f) for f in self._meta.key.key_fields.keys()}

    @classmethod
    def key_schema(cls):
        schema = cls.schema()
        for field in schema.get("properties").copy().keys():
            if field in cls._meta.key.key_fields.keys():
                continue
            schema["properties"].pop(field, None)

        return schema

    @classmethod
    def cast_to_type(cls, field, value):
        return cls.__fields__.get(field).type_(value)


def Model(key, indexes=None, table_name=None, owner_field=None):
    def wrapper(original_class):
        orig_init = original_class.__init__
        name = table_name or original_class.__name__
        original_class._meta = DynamodbMetadata(key, indexes, name, owner_field)

        def __init__(self, *args, **kws):
            orig_init(self, *args, **kws)

        original_class.__init__ = __init__
        return original_class

    return wrapper
