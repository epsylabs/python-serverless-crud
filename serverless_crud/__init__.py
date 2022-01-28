import os

from serverless_crud.aws.iam import DynamoDBPolicy
from serverless_crud.service import Manager

SERVICE_NAME = os.getenv("SERVICE_NAME", "api")
STAGE = os.getenv("STAGE", "current")

api = Manager(SERVICE_NAME, STAGE, DynamoDBPolicy())
