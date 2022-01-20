from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from serverless_crud.actions.base import Action
from serverless_crud.dynamodb import with_dynamodb
from serverless_crud.exceptions import EntityNotFoundException
from serverless_crud.model import BaseModel


class UpdateAction(Action):
    @with_dynamodb
    def handle(self, event: APIGatewayProxyEvent, context, table=None, dynamodb=None):
        payload = self._set_owner(event, event.json_body)

        obj: BaseModel = self._unpack(payload)
        query = dict(Item=obj.dict(), ReturnValues='NONE', )
        obj._meta.key.append_condition_expression(query, "attribute_exists")

        try:
            result = table.put_item(**query)

            return result, obj
        except dynamodb.exceptions.ConditionalCheckFailedException as e:
            return EntityNotFoundException()
