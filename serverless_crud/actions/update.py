from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from serverless_crud.actions.base import Action
from serverless_crud.dynamodb import with_dynamodb
from serverless_crud.exceptions import EntityNotFoundException
from serverless_crud.model import BaseModel


class UpdateAction(Action):
    @with_dynamodb
    def handle(self, primary_key, payload, event: APIGatewayProxyEvent, context, table=None, dynamodb=None):
        payload = self._set_owner(event, payload)

        obj: BaseModel = self._unpack(payload)
        query = dict(
            Key=primary_key.raw(),
            UpdateExpression="".join([f"SET #{k} = {k} " for k in payload.keys() if k not in primary_key.raw().keys()]),
            ExpressionAttributeNames={f"#{k}": k for k in payload.keys()},
            ExpressionAttributeValues={f":{k}": v for k, v in payload.items()},
            ReturnValues="NONE",
        )
        # obj._meta.key.append_condition_expression(query, "attribute_exists")

        print(query)

        try:
            result = table.update_item(**query)

            return result, obj.dict()
        except dynamodb.exceptions.ConditionalCheckFailedException as e:
            return EntityNotFoundException()
