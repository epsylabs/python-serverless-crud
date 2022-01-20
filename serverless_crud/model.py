from aws_lambda_powertools.utilities.parser import BaseModel as ParserBaseModel

from serverless_crud.dynamodb.annotation import DynamodbMetadata


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

            if field in schema["required"]:
                schema["required"].remove(field)

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
