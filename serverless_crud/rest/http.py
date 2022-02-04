import json
from typing import Optional, Dict

from aws_lambda_powertools.event_handler.api_gateway import Response


class JsonResponse(Response):
    def __init__(self, status_code: int, body: dict, headers: Optional[Dict] = None):
        super().__init__(status_code, "application/json", json.dumps(body), headers)
        self.raw_body = body
