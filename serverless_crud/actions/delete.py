from aws_lambda_powertools.event_handler.api_gateway import Response
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.validation import SchemaValidationError

from serverless_crud.actions.base import Action
from serverless_crud.dynamodb import with_dynamodb
from serverless_crud.utils import identity


class DeleteAction(Action):
    def append_delete_condition(self, params, event: APIGatewayProxyEvent):
        if not self.model._meta.owner_field:
            return

        params["ConditionExpression"] = f"#user = :user"
        params["ExpressionAttributeNames"] = {"#user": self.model._meta.owner_field}
        params["ExpressionAttributeValues"] = {":user": identity(event)}

    @with_dynamodb
    def handle(self, primary_key, event: APIGatewayProxyEvent, context, table, dynamodb):
        try:
            self.validate(primary_key.raw(), self.model.key_schema())

            params = dict(Key=primary_key.raw(), )

            self.append_delete_condition(params, event)

            return table.delete_item(**params)
        except SchemaValidationError as e:
            raise BadRequestError("Invalid request")
        except dynamodb.exceptions.ConditionalCheckFailedException as e:
            return Response(404, content_type="application/json", body="not found")
