import jwt
import stringcase


def identity(event):
    owner = "anon."
    try:
        if event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub"):
            owner = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
        elif event.get("identity", {}).get("claims", {}).get("sub"):
            owner = event.get("identity", {}).get("claims", {}).get("sub")
        elif "x-amz-security-token" in event.get("headers", {}) and "X-Authorization" in event.get("headers", {}):
            header = event.get("headers").get("X-Authorization")
            # it should be safe to ignore signature as request was authenticated via IAM, but it would be nice
            # to add verification at some point
            decoded = jwt.decode(header, options={"verify_signature": False})
            owner = decoded.get("sub")
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
