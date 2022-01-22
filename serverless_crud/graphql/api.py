import os

import graphene
import inflect
from graphene_pydantic import PydanticObjectType
from typing import List

from io import StringIO

from serverless_crud.api import BaseAPI
from serverless_crud.model import BaseModel


class GraphQLAPI(BaseAPI):
    def __init__(self, manager) -> None:
        super().__init__(manager)
        self.converted = StringIO()
        self.inflect_engine = inflect.engine()

    def handle(self, event, context):
        pass

    def registry(self, models, alias=None):
        if type(models) != list:
            models = [models]

        self._convert_models(models)

    def _create_model_app(self, model, alias, get_callback, create_callback, update_callback, delete_callback,
                          lookup_list_callback, lookup_scan_callback, lookup_query_callback):
        pass

    def render(self, output=None):
        if not output:
            output = os.path.join(os.getcwd(), "schema.graphql")
        with open(output, "w") as f:
            f.write(self.converted.getvalue())

    def _convert_models(self, models: List[BaseModel]):
        prepared = list(
            map(lambda model: type(model.__name__, (PydanticObjectType,), {"Meta": {"model": model}}), models)
        )

        self.converted.write(str(graphene.Schema(types=prepared)))
        for model in prepared:
            self.converted.write(
                """
type Query {
  get<<MODEL>>: <<MODEL>> @function(name: "FUNCTION-NAME")
  list<<MODEL_PLURAL>>: @function(name: "FUNCTION-NAME")
}""".replace("<<MODEL>>", model.__name__).replace("<<MODEL_PLURAL>>", self.inflect_engine.plural(model.__name__))
            )
