def identity(event):
    owner = "anon."
    try:
        owner = event.request_context.authorizer.claims["sub"]
    except KeyError:
        pass

    return owner
