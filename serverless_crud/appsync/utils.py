from functools import wraps

from serverless_crud.model import BaseModel
from serverless_crud.rest.http import JsonResponse


def response_handler(f):
    @wraps(f)
    def handler(*args, **kwargs):
        response, obj = f(*args, **kwargs)

        if isinstance(obj, JsonResponse):
            return obj.raw_body
        elif isinstance(obj, BaseModel):
            return obj.dict()
        else:
            return obj

    return handler
