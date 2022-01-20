from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from serverless_crud.actions.base import Action
from serverless_crud.dynamodb.utils import serializer
from serverless_crud.dynamodb import with_dynamodb


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
        obj = self._unpack(event.json_body)

        if self.model._meta.owner_field:
            self._query_index(f"by_{self.model._meta.owner_field}", event, table)
        else:
            self._scan_table(event, table)

        return event.json_body
