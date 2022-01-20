from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent, APIGatewayProxyEvent


def identity(event):
    owner = "anon."
    try:
        if isinstance(event, APIGatewayProxyEvent):
            owner = event.request_context.authorizer.claims["sub"]
        elif isinstance(event, AppSyncResolverEvent):
            print(type(event.identity))
            owner = event.identity.get("claims")
    except (KeyError, AttributeError):
        pass

    return owner
