from serverless_crud.actions import GetAction, CreateAction, UpdateAction, DeleteAction, ListAction
from serverless_crud.api import BaseAPI
from serverless_crud.builders.graphql import GraphqlBuilder


class GraphQLAPI(BaseAPI):
    def handle(self, event, context):
        pass

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self.graphql_builder = GraphqlBuilder()

    def registry(
        self,
        model,
        alias=None,
        get=GetAction,
        create=CreateAction,
        update=UpdateAction,
        delete=DeleteAction,
        lookup_list=ListAction,
    ):
        super().registry(model, alias, get, create, update, delete, lookup_list, None, None)
        self.graphql_builder.register(model, get, create, update, delete, lookup_list)

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
        pass

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
