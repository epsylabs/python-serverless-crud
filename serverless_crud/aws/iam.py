from serverless_crud.model import BaseModel

try:
    from troposphere import Sub
except ImportError:

    class Sub:
        def __init__(self, name):
            self.name = name

        def __str__(self):
            return self.name


class PolicyBuilder:
    def __init__(self, statements=None):
        statements = statements or []
        if isinstance(statements, dict):
            statements = [statements]
        self.statements = {statement.get("Sid"): statement for statement in statements}

    def get_statement(self, sid):
        return self.statements.get(sid)

    def add_statement(self, statement: dict):
        self.statements[statement.get("Sid")] = statement

    def registry(self, model: BaseModel):
        pass

    def all(self):
        return [
            statement for statement in self.statements.values() if statement.get("Action") and statement.get("Resource")
        ]


class DynamoDBPolicyBuilder(PolicyBuilder):
    def __init__(self):
        statements = {
            "Sid": "DynamodbTables",
            "Effect": "Allow",
            "Action": [
                "dynamodb:BatchGet*",
                "dynamodb:Get*",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:BatchWrite*",
                "dynamodb:Delete*",
                "dynamodb:Update*",
                "dynamodb:PutItem",
            ],
            "Resource": [],
        }

        super().__init__(statements)

    def registry(self, model: BaseModel):
        super().registry(model)

        self.get_statement("DynamodbTables").get("Resource").append(
            Sub(f"arn:aws:dynamodb:${{AWS::Region}}:${{AWS::AccountId}}:table/{model._meta.table_name}")
        )
        self.get_statement("DynamodbTables").get("Resource").append(
            Sub(f"arn:aws:dynamodb:${{AWS::Region}}:${{AWS::AccountId}}:table/{model._meta.table_name}/index/*")
        )
