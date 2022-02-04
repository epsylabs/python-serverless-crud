import abc
import json

from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.parser import parse, ValidationError
from aws_lambda_powertools.utilities.validation import validate

from serverless_crud.model import BaseModel
from serverless_crud.utils import identity


class Action(abc.ABC):
    def __init__(self, model):
        self.model: type(BaseModel) = model

    def __call__(self, *args, **kwargs):
        return self.handle(*args, **kwargs)

    def validate(self, payload, schema):
        return validate(event=payload, schema=schema)

    @abc.abstractmethod
    def handle(self, *args, **kwargs):
        pass

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
