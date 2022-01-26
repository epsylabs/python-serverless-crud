import json

from aws_lambda_powertools.event_handler.api_gateway import Response
from aws_lambda_powertools.event_handler.exceptions import NotFoundError, BadRequestError
from pydantic import ValidationError


class APIException(Exception):
    def __init__(self, http_code, message=None, json_body=None, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message
        self.http_code = http_code
        self.json_body = json_body

    def __str__(self):
        return self.message

    def as_response(self):
        return Response(
            self.http_code,
            content_type="application/json",
            body=json.dumps(self.json_body if self.json_body else {"message": self.msg}),
        )


class InvalidPayloadException(APIException, BadRequestError):
    def __init__(self, message="Invalid payload", *args: object) -> None:
        super().__init__(400, message, *args)


class DuplicatedEntityException(APIException, BadRequestError):
    def __init__(self, *args: object) -> None:
        super().__init__(409, message="Duplicated entity", *args)


class EntityNotFoundException(APIException, NotFoundError):
    def __init__(self, *args: object) -> None:
        super().__init__(404, message="Entity not found", *args)


class ValidationException(APIException, BadRequestError):
    def __init__(self, e: ValidationError, *args: object) -> None:
        super().__init__(400, json_body=e.errors(), *args)
