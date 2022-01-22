import stringcase
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent, APIGatewayProxyEvent


def identity(event):
    owner = "anon."
    try:
        if isinstance(event, APIGatewayProxyEvent):
            owner = event.request_context.authorizer.claims["sub"]
        elif isinstance(event, AppSyncResolverEvent):
            owner = event.identity.get("claims")["sub"]
    except (KeyError, AttributeError):
        pass

    return owner


class Identifier:
    def __init__(self, identifier):
        super().__init__()
        self.identifier = identifier

    @property
    def camel(self):
        return stringcase.camelcase(self.identifier)

    @property
    def pascal(self):
        return stringcase.pascalcase(self.identifier)

    @property
    def snake(self):
        return stringcase.snakecase(self.identifier)

    @property
    def spinal(self):
        return stringcase.spinalcase(self.identifier)

    @property
    def lower(self):
        return self.identifier.lower()

    def __str__(self):
        return self.identifier
