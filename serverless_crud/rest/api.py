from aws_lambda_powertools.event_handler import ApiGatewayResolver
from aws_lambda_powertools.event_handler.api_gateway import Router

from serverless_crud.api import BaseAPI
from serverless_crud.aws.iam import PolicyBuilder
from serverless_crud.exceptions import APIException
from serverless_crud.rest.utils import response_handler
from serverless_crud.utils import Identifier


class PrimaryKey:
    def __init__(self, **kwargs):
        self._values = kwargs

    def raw(self):
        return self._values

    def __repr__(self):
        return str(self._values)


class RestAPI(BaseAPI):
    def __init__(
        self, service_name: Identifier, policy_builder: PolicyBuilder = None, name: str = None, description: str = None
    ) -> None:
        super().__init__(service_name, policy_builder, name, description)
        self.app = ApiGatewayResolver(strip_prefixes=[f"/{self.name.spinal}"])

        @self.app.exception_handler(APIException)
        def handle_api_exception(ex: APIException):
            return ex.as_response()

    def handle(self, event, context):
        return self.app.resolve(event, context)

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
        router = Router()
        alias = alias.lower()

        id_route_pattern = f"/{alias}/<{model._meta.key.partition_key}>"
        if len(model._meta.key.key_fields) > 1:
            id_route_pattern += f"/<{model._meta.key.sort_key}>"

        if get_callback:

            @router.get(id_route_pattern)
            def get(*args, **kwargs):
                primary_key = model.primary_key_from_payload(kwargs)
                response, obj = get_callback(
                    *args, primary_key=primary_key, event=router.current_event, context=router.lambda_context
                )

                return obj

        if create_callback:

            @router.post(f"/{alias}")
            @response_handler(status_code=201)
            def create():
                return create_callback(
                    payload=router.current_event.json_body, event=router.current_event, context=router.lambda_context
                )

        if update_callback:

            @router.put(id_route_pattern)
            @response_handler(status_code=201)
            def update(*args, **kwargs):
                primary_key = model.primary_key_from_payload(kwargs)
                return update_callback(
                    primary_key=primary_key,
                    payload=router.current_event.json_body,
                    event=router.current_event,
                    context=router.lambda_context,
                )

        if delete_callback:

            @router.delete(id_route_pattern)
            @response_handler(status_code=200)
            def delete(*args, **kwargs):
                primary_key = PrimaryKey(**{k: model.cast_to_type(k, v) for k, v in kwargs.items()})
                return delete_callback(
                    *args, primary_key=primary_key, event=router.current_event, context=router.lambda_context
                )

        if lookup_list_callback:

            @response_handler(status_code=200)
            def lookup_list(index=None, *args, **kwargs):
                return lookup_list_callback(
                    index_name=index, event=router.current_event, context=router.lambda_context, *args, **kwargs
                )

            router.get(f"/lookup/{alias}/list/<index>")(lookup_list)
            router.get(f"/lookup/{alias}/list")(lookup_list)

        if lookup_scan_callback:

            @response_handler(status_code=200)
            def lookup_scan(*args, **kwargs):
                return lookup_scan_callback(event=router.current_event, context=router.lambda_context, *args, **kwargs)

            router.post(f"/lookup/{alias}/scan/<index>")(lookup_scan)
            router.post(f"/lookup/{alias}/scan")(lookup_scan)

        if lookup_query_callback:

            @response_handler(status_code=200)
            def lookup_query(*args, **kwargs):
                return lookup_query_callback(event=router.current_event, context=router.lambda_context, *args, **kwargs)

            router.post(f"/lookup/{alias}/query/<index>")(lookup_query)
            router.post(f"/lookup/{alias}/query")(lookup_query)

        self.app.include_router(router)

    def function(self, service, handler=None, **kwargs):
        if not self.models:
            return

        if self._function:
            return self._function

        handler = handler or f"{service.service.snake}.handlers.{self.name.snake}_handler"

        self._function = service.builder.function.http(
            self.name.spinal,
            self.description or "REST API",
            f"/{self.name.spinal}/{{proxy+}}",
            "ANY",
            handler=handler,
            role=f"arn:aws:iam::${{aws:accountId}}:role/{self.iam_execution_role_name()}",
            **kwargs,
        )

        return self._function
