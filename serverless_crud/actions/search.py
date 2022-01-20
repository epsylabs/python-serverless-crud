from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from pydantic import BaseModel, ValidationError

from serverless_crud.actions.base import Action
from serverless_crud.dynamodb import with_dynamodb
from serverless_crud.dynamodb.utils import serializer
from serverless_crud.exceptions import ValidationException


class SearchPayload(BaseModel):
    query: str
    parameters: dict


class SearchAction(Action):
    def validate(self, payload, schema):
        pass

    def _query_index(self, index, event, table):
        idx = self.model._meta.get_index(index)
        key = {f"#{k}": serializer.serialize(event.json_body.get(k)) for k, v in idx.fields.items()}
        key_names = {f"#{k}": k for k in idx.fields.keys()}

        table.query(
            Index=index,
            Limit=100,
            # KeyConditionExpression=,
            LastEvaluatedKey=event.json_body.get("_next", None)
        )

    def _scan_table(self, event, table):
        pass

    @with_dynamodb
    def handle(self, event: APIGatewayProxyEvent, context, dynamodb, table):
        try:
            payload = SearchPayload(**event.json_body)

            return event.json_body
        except ValidationError as e:
            raise ValidationException(e)
