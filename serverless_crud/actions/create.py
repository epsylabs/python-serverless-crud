from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from serverless_crud.actions.base import Action
from serverless_crud.dynamodb import with_dynamodb
from serverless_crud.exceptions import DuplicatedEntityException
from serverless_crud.logger import logger
from serverless_crud.model import BaseModel


class CreateAction(Action):
    @with_dynamodb
    def handle(self, payload, event: APIGatewayProxyEvent, context, table=None, dynamodb=None):
        try:
            payload = self._set_owner(event, payload)

            obj: BaseModel = self._unpack(payload)
            query = dict(
                Item=obj.dict(),
                ReturnValues="NONE",
            )
            obj._meta.key.append_condition_expression(query)

            logger.debug("dynamodb.put_item", extra=query)

            result = table.put_item(**query)

            return result, obj.dict()
        except dynamodb.exceptions.ConditionalCheckFailedException as e:
            raise DuplicatedEntityException()
