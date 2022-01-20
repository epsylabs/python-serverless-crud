from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from boto3.dynamodb.types import TypeDeserializer
from pydantic import BaseModel, ValidationError

from serverless_crud.actions.base import Action
from serverless_crud.dynamodb import with_dynamodb
from serverless_crud.dynamodb.annotation import KeyFieldTypes
from serverless_crud.dynamodb.utils import deserializer
from serverless_crud.exceptions import ValidationException, InvalidPayloadException
from serverless_crud.utils import identity


class SearchPayload(BaseModel):
    query: str
    parameters: dict
    _next: str = None


class SearchAction(Action):
    def _build_conditions(self, search: SearchPayload) -> dict:
        key_expressions = []
        filter_expressions = []
        attributes = {}
        for field, value in search.parameters.items():
            if field in self.model._meta.key.key_fields.keys():
                key_expressions.append(f"#{field} {value}")
            else:
                filter_expressions.append(f"#{field} {value}")

            attributes[f"#{field}"] = field

        if not attributes:
            return {}

        params = dict(
            ExpressionAttributeNames=attributes
        )

        if key_expressions:
            params["KeyConditionExpression"] = " and ".join(key_expressions)

        if filter_expressions:
            params["FilterExpression"] = " and ".join(filter_expressions)

        return params

    def _query_index(self, search: SearchPayload, event, table, dynamodb):
        idx = self.model._meta.get_index(search.query).name

        if not idx:
            raise InvalidPayloadException()

        query = dict(
            TableName=table.name,
            IndexName=idx,
            Limit=100,
            PaginationConfig={
                'MaxItems': 50,
                'StartingToken': search._next
            }
        )

        query.update(self._build_conditions(search))

        print(query)

        paginator = dynamodb.get_paginator("query")
        response = paginator.paginate(**query)

        return response

    def _scan_table(self, event, table):
        pass

    def _add_owner_condition(self, query, event):
        expression = query.get("KeyConditionExpression", "")
        if expression:
            expression += " and "

        query["KeyConditionExpression"] = expression + f"#{self.model._meta.owner_field} = :owner"
        attributes = query.get("ExpressionAttributeValues", {})
        attributes.update({":owner": identity(event)})
        query["ExpressionAttributeValues"] = attributes

        names = query.get("ExpressionAttributeNames", {})
        names.update({f"#{self.model._meta.owner_field}": self.model._meta.owner_field})
        query["ExpressionAttributeNames"] = names

    def _list_index(self, event, dynamodb, table, index, _next=None):
        owner_field = self.model._meta.owner_field
        if not owner_field or owner_field not in index.fields or index.fields.get(owner_field) != KeyFieldTypes.HASH:
            raise InvalidPayloadException("You can only use index listing with index hased by owner field")

        query = dict(
            TableName=table.name,
            IndexName=index.name,
            Limit=100,
        )

        self._add_owner_condition(query, event)

        response = table.query(**query)

        return response

    @with_dynamodb
    def handle(self, event: APIGatewayProxyEvent, context, dynamodb, table, index=None):
        try:
            if index:
                index = self.model._meta.get_index(index)
                response = self._list_index(event, dynamodb, table, index)
            else:
                payload = SearchPayload(**event.json_body)

                if payload.query == 'ALL':
                    response = self._scan_table(event, table)
                else:
                    response = self._query_index(payload, event, table, dynamodb)

            return response, [self.model(**result) for result in response["Items"]]
        except ValidationError as e:
            raise ValidationException(e)
