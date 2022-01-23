from functools import wraps

from serverless_crud.exceptions import APIException, ValidationException, EntityNotFoundException
from serverless_crud.logger import logger
from serverless_crud.model import BaseModel
from serverless_crud.rest.http import JsonResponse


def response_handler(f):
    @wraps(f)
    def handler(*args, **kwargs):
        try:
            response, obj = f(*args, **kwargs)

            if isinstance(obj, JsonResponse):
                return obj.raw_body
            elif isinstance(obj, BaseModel):
                return obj.dict()
            else:
                return obj
        except ValidationException as e:
            return {"kind": "validation"}
        except EntityNotFoundException as e:
            return {"kind": "404"}
        except APIException as e:
            logger.exception(e)

    return handler
