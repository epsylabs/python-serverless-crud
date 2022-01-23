from aws_lambda_powertools.metrics import SchemaValidationError
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from serverless_crud.actions.base import Action
from serverless_crud.dynamodb import with_dynamodb
from serverless_crud.exceptions import EntityNotFoundException
from serverless_crud.logger import logger
from serverless_crud.utils import identity


class GetAction(Action):
    @with_dynamodb
    def handle(self, primary_key, event: APIGatewayProxyEvent = None, context=None, table=None):
        try:
            self.validate(primary_key.raw(), self.model.key_schema())

            query = dict(
                Key=primary_key.raw(),
            )

            logger.debug("dynamodb.get_item", extra=query)
            response = table.get_item(**query)
            item = response.get("Item")

            if not item:
                raise EntityNotFoundException()

            if self.model._meta.owner_field and item.get(self.model._meta.owner_field) != identity(event):
                raise EntityNotFoundException()

            return response, item
        except SchemaValidationError as e:
            raise EntityNotFoundException()
