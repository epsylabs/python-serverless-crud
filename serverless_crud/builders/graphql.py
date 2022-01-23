import os
from io import StringIO

import graphene
import inflect
from graphene_pydantic import PydanticObjectType


class Transporter:
    def __init__(self, model_object, get, create, update, delete, lookup_list):
        self.model = model_object
        self.get = bool(get)
        self.create = bool(create)
        self.update = bool(update)
        self.delete = bool(delete)
        self.lookup_list = bool(lookup_list)

class GraphqlBuilder:
    def __init__(self):
        self.inflect_engine = inflect.engine()
        self.transporters = []

    def register(self, model, get=False, create=False, update=False, delete=False, lookup_list=False):
        self.transporters.append(Transporter(model, get, create, update, delete, lookup_list))

    def _build_model_type(self, model_name, model):
        return type(model_name, (PydanticObjectType,), {"Meta": {"model": model}})

    def _build(self):
        return list(
            map(lambda transporter: self._build_model_type(transporter.model.__name__, transporter.model), self.transporters)
        )

    def as_string(self):
        converted = StringIO()
        schema = graphene.Schema(types=self._build())

        converted.write(str(schema))

        queries = []
        mutations = []
        for transporter in self.transporters:
            model_name = transporter.model.__name__
            plural = self.inflect_engine.plural(model_name)
            if transporter.get:
                queries.append(
                    f'get{model_name}: {model_name} @function(name: "appsync")'
                )
            if transporter.lookup_list:
                converted.write("type <<MODEL>>List {\n".replace("<<MODEL>>", model_name))
                converted.write(f"items: [{model_name}]\nnextToken: String\n")
                converted.write("}\n")
                queries.append(f'list{plural}(nextToken: String): {model_name}List @function(name: "appsync")')

            if any((transporter.create, transporter.update)):
                converted.write(
                    str(graphene.Schema(types=[self._build_model_type(model_name+"Input", transporter.model)]))
                )
            for action in ("create", "update"):
                if getattr(transporter, action):
                    mutations.append(f'{action}{model_name}(input: {model_name}Input!): {model_name} @function(name: "appsync")')

            if transporter.delete:
                mutations.append(f'delete{model_name}(id: ID!): {model_name} @function(name: "appsync")')

        if queries:
            converted.write("type Query {\n")
            converted.write("\n".join(queries))
            converted.write("\n}\n")

        if mutations:
            converted.write("type Mutation {\n")
            converted.write("\n".join(mutations))
            converted.write("\n}\n")

        return converted.getvalue()

    def save_to_file(self):
        with open(os.path.join(os.getcwd(), "schema.graphql"), "w") as f:
            f.write(self.as_string())
