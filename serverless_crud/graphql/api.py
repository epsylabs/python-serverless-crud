from serverless_crud.actions import GetAction, CreateAction, UpdateAction, DeleteAction, ListAction
from serverless_crud.api import BaseAPI
from serverless_crud.aws.iam import PolicyBuilder
from serverless_crud.builders.graphql import SchemaBuilder
from serverless_crud.utils import Identifier


class GraphQLAPI(BaseAPI):
    def __init__(
        self, service_name: Identifier, policy_builder: PolicyBuilder = None, name: str = None, description: str = None
    ) -> None:
        super().__init__(service_name, policy_builder, name, description)
        self.schema_builder = SchemaBuilder()

    def handle(self, event, context):
        schema = self.schema_builder.schema()

        return schema.execute(event.get("body"), context=dict(event=event, context=context))

    def registry(
        self,
        model,
        alias=None,
        get=GetAction,
        create=CreateAction,
        update=UpdateAction,
        delete=DeleteAction,
        lookup_list=ListAction,
        **kwargs,
    ):
        super().registry(model, alias, get, create, update, delete, lookup_list, None, None)

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

        handlers = {}
        if get_callback:

            def handler_get(parent, info, *args, **kwargs):
                primary_key = model.primary_key_from_payload(kwargs)
                output_type = self.schema_builder.get_type(model)
                response, obj = get_callback(
                    primary_key=primary_key, event=info.context.get("event"), context=info.context.get("context")
                )
                return output_type(**obj)

            handlers["get"] = handler_get

        if create_callback:

            def handler_create(parent, info, *args, **kwargs):
                output_type = self.schema_builder.get_type(model)
                response, obj = create_callback(event=info.context.get("event"), context=info.context.get("context"))

                return output_type(**obj)

            handlers["create"] = handler_create

        if update_callback:

            def handler_update(parent, info, *args, **kwargs):
                primary_key = model.primary_key_from_payload(kwargs)
                output_type = self.schema_builder.get_type(model)
                response, obj = update_callback(
                    primary_key=primary_key, event=info.context.get("event"), context=info.context.get("context")
                )

                return output_type(**obj)

            handlers["update"] = handler_update

        if delete_callback:

            def handler_delete(parent, info, *args, **kwargs):
                primary_key = model.primary_key_from_payload(kwargs)
                output_type = self.schema_builder.get_type(model)
                response, obj = delete_callback(
                    primary_key=primary_key, event=info.context.get("event"), context=info.context.get("context")
                )

                return output_type(**obj)

            handlers["delete"] = handler_delete

        if lookup_list_callback:

            def handler_lookup_list(parent, info, *args, **kwargs):
                output_type = self.schema_builder.get_type(model)

                response, obj = lookup_list_callback(
                    event=info.context.get("event"), context=info.context.get("context")
                )

                return list(map(lambda x: output_type(**x), obj))

            handlers["lookup_list"] = handler_lookup_list

        self.schema_builder.registry(model, **handlers)

    def function(self, service, handler=None, **kwargs):
        if not self.models:
            return

        if self._function:
            return self._function

        handler = f"{service.service.snake}.handlers.{self.name.snake}_handler"

        self._function = service.builder.function.http(
            self.name.spinal,
            self.description or "GraphQL API",
            f"/{self.name.spinal}",
            "ANY",
            handler=handler,
            role=f"arn:aws:iam::${{aws:accountId}}:role/{self.iam_execution_role_name()}",
            **kwargs,
        )

        return self._function
