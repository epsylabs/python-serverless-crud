import abc

from serverless_crud.actions import *
from serverless_crud.actions.search import ListAction, ScanAction, QueryAction
from serverless_crud.aws.iam import PolicyBuilder
from serverless_crud.utils import Identifier

try:
    from troposphere import Sub
except ImportError:

    class Sub:
        def __init__(self, name):
            self.name = name

        def __str__(self):
            return self.name


class BaseAPI(abc.ABC):
    def __init__(
        self, service_name: Identifier, policy_builder: PolicyBuilder = None, name: str = None, description: str = None
    ):
        self.models = []
        self.service_name = service_name
        self.policy_builder = policy_builder
        self.name = Identifier(name or type(self).__name__.lower().replace("api", ""))
        self.description = description
        self._function = None

    @abc.abstractmethod
    def handle(self, event, context):
        pass

    def registry(
        self,
        model,
        alias=None,
        get=GetAction,
        create=CreateAction,
        update=UpdateAction,
        delete=DeleteAction,
        lookup_list=ListAction,
        lookup_scan=ScanAction,
        lookup_query=QueryAction,
        **kwargs,
    ):
        self.models.append(model)
        self.policy_builder.registry(model)
        alias = alias or model.__name__
        self._create_model_app(
            model,
            alias,
            get_callback=get(model) if get else None,
            create_callback=create(model) if create else None,
            update_callback=update(model) if update else None,
            delete_callback=delete(model) if delete else None,
            lookup_list_callback=lookup_list(model) if lookup_list else None,
            lookup_scan_callback=lookup_scan(model) if lookup_scan else None,
            lookup_query_callback=lookup_query(model) if lookup_query else None,
        )

    @abc.abstractmethod
    def _create_model_app(
        self,
        model,
        alias,
        get_callback,
        create_callback,
        update_callback,
        delete_callback,
        lookup_list_callback,
        lookup_scan_callback,
        lookup_query_callback,
    ):
        pass

    def resources(self, service=None):
        from troposphere import dynamodb, iam
        from serverless_crud.dynamodb.builder import model_to_table_specification

        if not self.models:
            return []

        resources = []
        for model in self.models:
            resources.append(dynamodb.Table(model._meta.table_name, **model_to_table_specification(model)))

        statements = self.policy_builder.all()

        try:
            statements += service.provider.iam.statements
        except AttributeError as e:
            raise e
            pass

        if not statements:
            return resources

        role = iam.Role(
            f"{self.name.pascal}ExecutionRole",
            AssumeRolePolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}
                ],
            },
            ManagedPolicyArns=["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"],
            Policies=[
                iam.Policy(
                    "Policy", PolicyName="Policy", PolicyDocument={"Version": "2012-10-17", "Statement": statements}
                )
            ],
            RoleName=Sub(self.iam_execution_role_name()),
        )

        resources.append(role)

        return resources

    @abc.abstractmethod
    def function(self, service, handler=None, **kwargs):
        pass

    def iam_execution_role_name(self):
        return f"{self.service_name.spinal}-${{aws:region}}-${{sls:stage}}-{self.name.lower}-role"

    def __call__(self, event, context, *args, **kwargs):
        return self.handle(event, context)
