from serverless_crud.actions import GetAction, CreateAction, UpdateAction, DeleteAction, ListAction
from serverless_crud.api import BaseAPI
from serverless_crud.graphql.builder import SchemaBuilder


class GraphQLAPI(BaseAPI):
    def handle(self, event, context):
        schema = self.builder.schema()

        return schema.execute(event.get("body"), context=dict(event=event, context=context))

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self.builder = SchemaBuilder()

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
                try:
                    primary_key = model.primary_key_from_payload(kwargs)
                    response, obj = get_callback(
                        primary_key=primary_key,
                        event=info.context.get("event"),
                        context=info.context.get("context")
                    )

                    return obj
                except Exception as e:
                    pass

                return None

            handlers["get"] = handler_get

        if create_callback:
            def handler_create(parent, info, *args, **kwargs):
                return {
                    "created": 1231231,
                    "id": "234234234",
                    "user": "asdfadfasdf"
                }

            handlers["create"] = handler_create

        if update_callback:
            def handler_update(parent, info, *args, **kwargs):
                return {
                    "created": 1231231,
                    "id": "234234234",
                    "user": "asdfadfasdf"
                }

            handlers["update"] = handler_update

        if delete_callback:
            def handler_delete(parent, info, *args, **kwargs):
                return {
                    "created": 1231231,
                    "id": "234234234",
                    "user": "asdfadfasdf"
                }

            handlers["delete"] = handler_delete

        if lookup_list_callback:
            def handler_lookup_list(parent, info, *args, **kwargs):
                return {
                    "created": 1231231,
                    "id": "234234234",
                    "user": "asdfadfasdf"
                }

            handlers["lookup_list"] = handler_lookup_list

        self.builder.registry(model, **handlers)

    def schema(self):
        return self.builder.schema()

    def function(self, service, handler=None, **kwargs):
        if not self.models:
            return

        if self._function:
            return self._function

        handler = f"{service.service.snake}.handlers.graphql_handler"

        self._function = service.builder.function.http(
            "graphql",
            "GraphQL API",
            "/graphql",
            "ANY",
            handler=handler,
            role=f"arn:aws:iam::${{aws:accountId}}:role/{self.iam_execution_role_name()}",
            **kwargs,
        )

        return self._function
