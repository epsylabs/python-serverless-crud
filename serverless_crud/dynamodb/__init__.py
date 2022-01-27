import inspect
from functools import wraps

import boto3


def with_dynamodb(f):
    @wraps(f)
    def wrapper(self, *args, **kwds):
        sig = inspect.signature(f)

        if not hasattr(f, "dynamodb"):
            setattr(f, "dynamodb", boto3.client("dynamodb"))

        dynamodb = getattr(f, "dynamodb")

        if "dynamodb" in sig.parameters:
            kwds["dynamodb"] = dynamodb

        if "table" in sig.parameters:
            kwds["table"] = boto3.resource("dynamodb").Table(self.model._meta.table_name)

        return f(self, *args, **kwds)

    return wrapper
