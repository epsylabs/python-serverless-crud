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
