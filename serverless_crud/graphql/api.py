import os
from io import StringIO
from typing import List

import graphene
import inflect
from graphene_pydantic import PydanticObjectType

from serverless_crud.api import BaseAPI
from serverless_crud.model import BaseModel


class GraphQLAPI(BaseAPI):
    def __init__(self, manager) -> None:
        super().__init__(manager)
        self.inflect_engine = inflect.engine()

    def handle(self, event, context):
        pass

    def registry(self, model, **kwargs):
        self.models.append(model)

    def _create_model_app(self, model, alias, get_callback, create_callback, update_callback, delete_callback,
                          lookup_list_callback, lookup_scan_callback, lookup_query_callback):
        pass

    def function(self, service, handler=None, **kwargs):
        if not self.models:
            return

        handler = f"{service.service.snake}.handlers.graphql_handler"

        return service.builder.function.http("graphql", "GraphQL API", "/graphql", "ANY", handler=handler, **kwargs)

    def render(self, output=None):
        converted = self._convert_models(self.models)

        if not output:
            output = os.path.join(os.getcwd(), "schema.graphql")
        with open(output, "w") as f:
            f.write(converted.getvalue())

    def _convert_models(self, models: List[BaseModel]):
        converted = StringIO()
        prepared = list(
            map(lambda model: type(model.__name__, (PydanticObjectType,), {"Meta": {"model": model}}), models)
        )

        converted.write(str(graphene.Schema(types=prepared)))
        for model in prepared:
            converted.write(
                """
type Query {
  get<<MODEL>>: <<MODEL>> @function(name: "FUNCTION-NAME")
  list<<MODEL_PLURAL>>: @function(name: "FUNCTION-NAME")
}""".replace("<<MODEL>>", model.__name__).replace("<<MODEL_PLURAL>>", self.inflect_engine.plural(model.__name__))
            )
        return converted
