import abc

from serverless_crud.actions import *
from serverless_crud.actions.search import ListAction, ScanAction, QueryAction
from serverless_crud.dynamodb.builder import model_to_table_specification


class API(abc.ABC):
    def __init__(self):
        self.models = []

    @abc.abstractmethod
    def handle(self, event, context):
        pass

    def registry(self, model, alias=None, get=GetAction, create=CreateAction, update=UpdateAction, delete=DeleteAction,
                 lookup_list=ListAction, lookup_scan=ScanAction, lookup_query=QueryAction):
        self.models.append(model)
        alias = alias or model.__name__
        self._create_model_app(
            model, alias,
            get_callback=get(model) if get else None,
            create_callback=create(model) if create else None,
            update_callback=update(model) if update else None,
            delete_callback=delete(model) if delete else None,
            lookup_list_callback=lookup_list(model) if lookup_list else None,
            lookup_scan_callback=lookup_scan(model) if lookup_scan else None,
            lookup_query_callback=lookup_query(model) if lookup_query else None,
        )

    @abc.abstractmethod
    def _create_model_app(self, model, alias, get_callback, create_callback, update_callback, delete_callback,
                          lookup_list_callback, lookup_scan_callback, lookup_query_callback):
        pass

    def resources(self):
        from troposphere import dynamodb, iam

        resources = []
        dynamodb_names = []
        for model in self.models:
            dynamodb_names.append(f"table/{model._meta.table_name}")
            dynamodb_names.append(f"table/{model._meta.table_name}/index/*")
            resources.append(dynamodb.Table(model._meta.table_name, **model_to_table_specification(model)))

        role = iam.Role(
            "Role",
            AssumeRolePolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            },
            Description="API lambda execution role",
            Policies=[
                iam.Policy(
                    "Policy",
                    PolicyName="Policy",
                    PolicyDocument={
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Sid": "SpecificTable",
                                "Effect": "Allow",
                                "Action": [
                                    "dynamodb:BatchGet*",
                                    "dynamodb:Get*",
                                    "dynamodb:Query",
                                    "dynamodb:Scan",
                                    "dynamodb:BatchWrite*",
                                    "dynamodb:Delete*",
                                    "dynamodb:Update*",
                                    "dynamodb:PutItem"
                                ],
                                "Resource": [
                                    f"arn:aws:dynamodb:${{AWS::Region}}:${{AWS::AccountId}}:{name}" for name in dynamodb_names
                                ]
                            }
                        ]
                    }
                )
            ],
            RoleName="us-east-1-service-role"
        )

        return resources

    def __call__(self, event, context, *args, **kwargs):
        return self.handle(event, context)
