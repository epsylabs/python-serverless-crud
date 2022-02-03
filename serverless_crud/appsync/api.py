import logging

from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.event_handler.appsync import Router

from serverless_crud.api import BaseAPI
from serverless_crud.appsync.utils import response_handler
from serverless_crud.aws.iam import PolicyBuilder
from serverless_crud.builders.graphql import AppSyncSchemaBuilder
from serverless_crud.utils import Identifier


def dummy_handler(*args, **kwargs):
    pass


class AppSyncAPI(BaseAPI):
    def __init__(
        self, service_name: Identifier, policy_builder: PolicyBuilder = None, name: str = None, description: str = None
    ) -> None:
        super().__init__(service_name, policy_builder, name, description)
        self.app = AppSyncResolver()
        self.schema_builder = AppSyncSchemaBuilder()

    def handle(self, event, context):
        return self.app.resolve(event, context)

    def function(self, service, handler=None, **kwargs):
        if not self.models:
            return

        if self._function:
            return self._function

        handler = handler or f"{service.service.snake}.handlers.{self.name.snake}_handler"

        self._function = service.builder.function.generic(
            self.name.spinal,
            self.description or "AppSync API resolver",
            handler=handler,
            role=f"arn:aws:iam::${{aws:accountId}}:role/{self.iam_execution_role_name()}",
            **kwargs,
        )

        return self._function

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
        handlers = {}

        if get_callback:
            @router.resolver(type_name="Query", field_name=f"get{alias}")
            @response_handler
            def get(*args, **kwargs):
                primary_key = model.primary_key_from_payload(kwargs)
                return get_callback(
                    *args, **kwargs, primary_key=primary_key, event=router.current_event, context=router.lambda_context
                )

            handlers["get"] = get

        if create_callback:

            @router.resolver(type_name="Mutation", field_name=f"create{alias}")
            @response_handler
            def create(input, *args, **kwargs):
                return create_callback(payload=input, event=router.current_event, context=router.lambda_context)

            handlers["create"] = create

        if update_callback:

            @router.resolver(type_name="Mutation", field_name=f"update{alias}")
            @response_handler
            def update(input, *args, **kwargs):
                primary_key = model.primary_key_from_payload(input)

                return update_callback(
                    primary_key=primary_key, payload=input, event=router.current_event, context=router.lambda_context
                )

            handlers["update"] = update

        if delete_callback:

            @router.resolver(type_name="Mutation", field_name=f"delete{alias}")
            @response_handler
            def delete(*args, **kwargs):
                primary_key = model.primary_key_from_payload(kwargs)
                return delete_callback(
                    *args, primary_key=primary_key, event=router.current_event, context=router.lambda_context
                )

            handlers["delete"] = delete

        if lookup_list_callback:

            @router.resolver(type_name="Query", field_name=f"list{alias}")
            @response_handler
            def lookup_list(index=None, *args, **kwargs):
                if not index:
                    try:
                        index = next(
                            iter(
                                [
                                    idx.name
                                    for idx in getattr(model._meta, "indexes", [])
                                    if idx.partition_key == model._meta.owner_field
                                ]
                            )
                        )
                    except StopIteration:
                        logging.info("We were unable to find partition key.")
                        index = None

                return lookup_list_callback(
                    index_name=index, event=router.current_event, context=router.lambda_context, *args, **kwargs
                )

            handlers["lookup_list"] = lookup_list

        self.app.include_router(router)
        self.schema_builder.registry(model, **handlers)
