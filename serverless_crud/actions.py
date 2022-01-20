import abc
import json

from aws_lambda_powertools.event_handler.api_gateway import Response
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.parser import parse, ValidationError
from aws_lambda_powertools.utilities.validation import validate, SchemaValidationError
from boto3.dynamodb.types import TypeSerializer

from serverless_crud.dynamodb import with_dynamodb
from serverless_crud.model import BaseModel
from serverless_crud.utils import identity

serializer = TypeSerializer()


class Action(abc.ABC):
    def __init__(self, model):
        self.model: BaseModel = model

    def __call__(self, *args, **kwargs):
        return self.handle(*args, **kwargs)

    def validate(self, payload, schema):
        return validate(event=payload, schema=schema)

    @abc.abstractmethod
    def handle(self, *args, **kwargs):
        pass

    def _fetch_item(self, table, primary_key, fields=None):
        params = dict(
            Key=primary_key.raw(),
        )

        if fields:
            params["AttributesToGet"] = fields

        return table.get_item(**params).get("Item")

    def _set_owner(self, event: APIGatewayProxyEvent, payload: dict):
        if not self.model._meta.owner_field:
            return payload

        payload[self.model._meta.owner_field] = identity(event)

        return payload

    def _unpack(self, payload):
        try:
            parsed_payload: BaseModel = parse(model=self.model, event=payload)

            return parsed_payload
        except ValidationError as e:
            raise BadRequestError(json.dumps({"status_code": 400, "message": e.errors()}))


class CreateAction(Action):
    @with_dynamodb
    def handle(self, event: APIGatewayProxyEvent, context, table=None, dynamodb=None):
        payload = self._set_owner(event, event.json_body)

        obj: BaseModel = self._unpack(payload)
        query = dict(Item=obj.dict(), ReturnValues='NONE', )
        obj._meta.key.append_condition_expression(query)

        try:
            result = table.put_item(**query)

            return result, obj
        except dynamodb.exceptions.ConditionalCheckFailedException as e:
            return Response(409, content_type="application/json", body="duplicated")


class UpdateAction(Action):
    @with_dynamodb
    def handle(self, event: APIGatewayProxyEvent, context, table=None, dynamodb=None):
        payload = self._set_owner(event, event.json_body)
        print(payload)

        obj: BaseModel = self._unpack(payload)
        query = dict(Item=obj.dict(), ReturnValues='NONE', )
        obj._meta.key.append_condition_expression(query, "attribute_exists")

        try:
            result = table.put_item(**query)

            return result
        except dynamodb.exceptions.ConditionalCheckFailedException as e:
            return Response(404, content_type="application/json", body="not found")


class GetAction(Action):
    @with_dynamodb
    def handle(self, primary_key, event: APIGatewayProxyEvent = None, context=None, table=None):
        try:
            self.validate(primary_key.raw(), self.model.key_schema())

            item = self._fetch_item(table, primary_key)

            return item
        except SchemaValidationError as e:
            raise BadRequestError("Invalid request")


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
