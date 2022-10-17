import logging
from functools import wraps

from serverless_crud.model import BaseModel
from serverless_crud.rest.http import JsonResponse

from pydantic import ValidationError


def response_handler(f):
    @wraps(f)
    def handler(*args, **kwargs):
        try:
            response, obj = f(*args, **kwargs)
        except ValidationError as e:
            return dict(
                errorType="ValidationError",
                errorMessage=str(e)
            )
        except TypeError as e:
            response = None
            obj = None
            logging.info(f'Handler function "{f}" did not return any data.')

        if isinstance(obj, JsonResponse):
            return obj.raw_body
        elif isinstance(obj, BaseModel):
            return obj.dict()
        else:
            return obj

    return handler
