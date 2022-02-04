from aws_lambda_powertools.utilities.parser import BaseModel as ParserBaseModel

from serverless_crud.dynamodb.annotation import DynamodbMetadata


class PrimaryKey:
    def __init__(self, **kwargs):
        self._values = kwargs

    def raw(self):
        return self._values

    def __repr__(self):
        return str(self._values)


class BaseModel(ParserBaseModel):
    _meta: DynamodbMetadata = None

    def _field_type(self, field):
        return self.__fields__.get(field).type

    def get_primary_key(self):
        return {f: getattr(self, f) for f in self._meta.key.key_fields.keys()}

    @classmethod
    def filter_by(cls):
        """
        List of fields you can filter model by. By default, all fields are returned.
        """
        return cls.schema().get("properties", {}).keys()

    @classmethod
    def primary_key_from_payload(cls, payload):
        return PrimaryKey(**{f: payload.get(f) for f in cls._meta.key.key_fields.keys()})

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
