import os
import re
from io import StringIO
from pathlib import Path

import graphene
import inflect
from graphene_pydantic import PydanticObjectType


import uuid

import graphene
from graphene_pydantic import PydanticObjectType, PydanticInputObjectType


class SchemaBuilder:
    def __init__(self):
        self.models = {}
        self.output_type = {}

    def registry(self, model, /, **actions):
        self.models[model] = actions

    def build_schema(self):
        query_fields = {}
        mutation_fields = {}
        for model in self.models.keys():
            model_dto, input_dto = self.build_types(model.__name__, model)
            query_fields.update(self.build_query_fields(model_dto, model))
            mutation_fields.update(self.build_mutation_fields(model_dto, input_dto, model))

            self.output_type[model] = model_dto

        Query = type("Query", (graphene.ObjectType,), query_fields)

        Mutation = type("Mutation", (graphene.ObjectType,), mutation_fields)

        return dict(query=Query, mutation=Mutation)

    def build_types(self, model_name, model_type):
        return (
            type(model_name, (PydanticObjectType,), {"Meta": {"model": model_type}}),
            type(f"{model_name}Input", (PydanticInputObjectType,), {"Meta": {"model": model_type}}),
        )

    def build_query_fields(self, model_dto, model):
        queries = {}

        if self.models[model].get("get"):
            queries.update(
                {
                    f"get{model.__name__}": graphene.Field(model_dto, id=graphene.String(required=True)),
                    f"resolve_get{model.__name__}": self.models[model].get("get"),
                }
            )

        if self.models[model].get("lookup_list"):
            queries.update(
                {
                    f"list{model.__name__}": graphene.Field(model_dto),
                    f"resolve_list{model.__name__}": self.models[model].get("lookup_list"),
                }
            )

        return queries

    def build_mutation_fields(self, model_dto, input_dto, model):
        def mutate_(parent, info, input):
            return model(id=str(uuid.uuid4()), created=23423423, user=str(uuid.uuid4()))

        InputArguments = type("Arguments", (), {"input": input_dto(required=True), "nextToken": graphene.String()})
        IdArguments = type("Arguments", (), {"id": graphene.String(required=True)})

        mutations = {}

        if self.models[model].get("create"):
            Create = type(
                f"Create{model.__name__}",
                (graphene.Mutation,),
                {"Arguments": InputArguments, "Output": model_dto, "mutate": mutate_},
            )
            mutations[f"create{model.__name__}"] = Create.Field()

        if self.models[model].get("update"):
            Update = type(
                f"Update{model.__name__}",
                (graphene.Mutation,),
                {"Arguments": InputArguments, "Output": model_dto, "mutate": mutate_},
            )
            mutations[f"update{model.__name__}"] = Update.Field()

        if self.models[model].get("delete"):
            Delete = type(
                f"Delete{model.__name__}",
                (graphene.Mutation,),
                {"Arguments": IdArguments, "Output": model_dto, "mutate": mutate_},
            )
            mutations[f"delete{model.__name__}"] = Delete.Field()

        return mutations

    def get_type(self, model):
        return self.output_type.get(model)

    def schema(self):
        return graphene.Schema(**self.build_schema())

    def render(self, output=None):
        if output:
            output.write(str(self.dump()))
            return

        import __main__ as main

        with open(Path(main.__file__).stem, "w+") as f:
            f.write(str(self.dump()))

    def dump(self):
        return str(self.schema())


class AppSyncSchemaBuilder(SchemaBuilder):
    def __init__(self):
        super().__init__()
        self.handler = "appsync"

    def dump(self):
        gql = super().dump()

        global_regex = r"(type\s+(Query|Mutation)\s+{(?P<definitions>.*?)})"
        definition_regex = r"^(.+)$"

        matches = re.finditer(global_regex, gql, re.MULTILINE | re.VERBOSE | re.DOTALL)
        for m in matches:
            block = m.groupdict().get("definitions")
            for definition in re.findall(definition_regex, block, re.MULTILINE):
                block = block.replace(definition, f"{definition} @function(name: \"{self.handler}\")")

            gql = gql.replace(m.groupdict().get("definitions"), block)

        return gql

    def render(self, output=None, handler=None):
        self.handler = handler or "appsync"
        super().render(output)
