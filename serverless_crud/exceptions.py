class APIException(Exception):
    def __init__(self, http_code, message, *args: object) -> None:
        super().__init__(*args)
        self.http_code = http_code
        self.message = message


class InvalidPayloadException(APIException):
    def __init__(self, message="Invalid payload", *args: object) -> None:
        super().__init__(400, message, *args)
