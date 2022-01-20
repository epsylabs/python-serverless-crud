from aws_lambda_powertools.metrics import SchemaValidationError
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from serverless_crud.actions.base import Action
from serverless_crud.dynamodb import with_dynamodb
from serverless_crud.exceptions import EntityNotFoundException


class GetAction(Action):
    @with_dynamodb
    def handle(self, primary_key, event: APIGatewayProxyEvent = None, context=None, table=None):
        try:
            self.validate(primary_key.raw(), self.model.key_schema())

            params = dict(
                Key=primary_key.raw(),
            )

            respose = table.get_item(**params)

            return respose, self.model(**respose.get("Item"))
        except SchemaValidationError as e:
            raise EntityNotFoundException()
