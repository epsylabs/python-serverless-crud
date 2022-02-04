from functools import wraps

from aws_lambda_powertools.event_handler.api_gateway import Response

from serverless_crud.model import BaseModel
from serverless_crud.rest.http import JsonResponse


def response_handler(status_code=200):
    def wrapper(f):
        @wraps(f)
        def handler(*args, **kwargs):
            response, obj = f(*args, **kwargs)

            if isinstance(obj, Response):
                return obj
            elif isinstance(obj, BaseModel):
                return obj
            elif isinstance(obj, dict):
                return JsonResponse(status_code, body=obj)
            else:
                return obj or {}

        return handler

    return wrapper
