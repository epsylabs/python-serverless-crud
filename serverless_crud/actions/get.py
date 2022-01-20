from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.metrics import SchemaValidationError
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from serverless_crud.actions.base import Action
from serverless_crud.dynamodb import with_dynamodb


class GetAction(Action):
    @with_dynamodb
    def handle(self, primary_key, event: APIGatewayProxyEvent = None, context=None, table=None):
        try:
            self.validate(primary_key.raw(), self.model.key_schema())

            item = self._fetch_item(table, primary_key)

            return item
        except SchemaValidationError as e:
            raise BadRequestError("Invalid request")
