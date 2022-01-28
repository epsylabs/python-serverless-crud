from serverless_crud.aws.iam import DynamoDBPolicy
from serverless_crud.service import Manager


api = Manager(DynamoDBPolicy())
