import abc
import re
from abc import ABC
from typing import Optional

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from pydantic import BaseModel, ValidationError

from serverless_crud.actions.base import Action
from serverless_crud.dynamodb import with_dynamodb
from serverless_crud.dynamodb.annotation import KeyFieldTypes, DynamoIndex
from serverless_crud.exceptions import ValidationException, InvalidPayloadException
from serverless_crud.logger import logger
from serverless_crud.utils import identity


class ScanPayload(BaseModel):
    expression: str = None
    values: dict = None
    checkOwner: bool = True


class QueryPayload(BaseModel):
    key_expression: str
    filter_expression: str = None
    values: dict = None
    checkOwner: bool = True


class SearchAction(Action, ABC):
    def _get_query_target(self, table, index: Optional[DynamoIndex]):
        if index:
            return dict(IndexName=index.name)
        else:
            return dict(TableName=table.name)

    def _get_owner_condition_placement(self):
        pass

    def _add_owner_condition(self, query, event, owner_filter_namespace="KeyConditionExpression"):
        expression = query.get(owner_filter_namespace, "")
        if expression:
            expression = f"( {expression}  ) and "

        query[owner_filter_namespace] = expression + f"#{self.model._meta.owner_field} = :owner"
        attributes = query.get("ExpressionAttributeValues", {})
        attributes.update({":owner": identity(event)})
        query["ExpressionAttributeValues"] = attributes

        names = query.get("ExpressionAttributeNames", {})
        names.update({f"#{self.model._meta.owner_field}": self.model._meta.owner_field})
        query["ExpressionAttributeNames"] = names

    @abc.abstractmethod
    def _fetch_items(self, event, dynamodb, table, index):
        pass

    def _extract_fields(self, expression):
        regex = r"#[\w\d]+"
        matches = re.findall(regex, expression)

        return {m: m.strip("#") for m in matches}

    @with_dynamodb
    def handle(self, event: APIGatewayProxyEvent, context, dynamodb, table, index_name=None):
        try:
            index = self.model._meta.get_index(index_name)
            response = self._fetch_items(event, dynamodb, table, index)

            return response, dict(
                items=[self.model(**i).dict() for i in response["Items"]], nextToken=response.get("LastEvaluatedKey")
            )
        except ValidationError as e:
            raise ValidationException(e)


class ScanAction(SearchAction):
    def _fetch_items(self, event, dynamodb, table, index, _next=None):
        payload = ScanPayload(**event.json_body)

        query = {**dict(Limit=100), **self._get_query_target(table, index)}

        if payload.expression:
            query.update(
                dict(
                    FilterExpression=payload.expression,
                    ExpressionAttributeNames=self._extract_fields(str(payload.expression)),
                    ExpressionAttributeValues=payload.values,
                )
            )

        if payload.checkOwner:
            self._add_owner_condition(query, event, "FilterExpression")

        logger.debug("dynamodb.scan", extra=query)

        return table.scan(**query)


class QueryAction(SearchAction):
    def _fetch_items(self, event, dynamodb, table, index, _next=None):
        payload = QueryPayload(**event.json_body)

        expression = str(payload.filter_expression) + " " + str(payload.key_expression)

        query = {
            **dict(Limit=100),
            **dict(
                KeyConditionExpression=payload.key_expression,
                ExpressionAttributeNames=self._extract_fields(expression),
                ExpressionAttributeValues=payload.values,
            ),
            **self._get_query_target(table, index),
        }

        if payload.filter_expression:
            query["FilterExpression"] = payload.filter_expression

        if payload.checkOwner:
            self._add_owner_condition(query, event, "FilterExpression")

        logger.debug("dynamodb.query", extra=query)

        return table.query(**query)


class ListAction(SearchAction):
    def validate(self, index, **kwargs):
        owner_field = self.model._meta.owner_field

        is_owner_field_pk = self.model._meta.key.partition_key == owner_field
        is_owner_part_of_index = index and index.fields.get(owner_field) == KeyFieldTypes.HASH

        if not (is_owner_field_pk or is_owner_part_of_index):
            raise InvalidPayloadException(
                "You can only use list method only on tables or indexes with record owner for partition key"
            )

    def _fetch_items(self, event, dynamodb, table, index, _next=None):
        self.validate(index)

        query = {**dict(Limit=100), **self._get_query_target(table, index)}

        self._add_owner_condition(query, event)

        logger.debug("dynamodb.query", extra=query)

        return table.query(**query)
