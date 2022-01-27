import os

from serverless_crud.appsync import AppSyncAPI
from serverless_crud.graphql import GraphQLAPI
from serverless_crud.rest import RestAPI
from serverless_crud.utils import Identifier


class Manager:
    def __init__(self):
        self.apis = dict(rest=RestAPI(self), graphql=GraphQLAPI(self), appsync=AppSyncAPI(self))

        self.service_name = Identifier(os.getenv("SERVICE_NAME", "api"))
        self.stage = os.getenv("STAGE", "current")

    def resources(self, service=None):
        resources = []

        for api in self.apis.values():
            resources += api.resources(service=service)

        return resources

    def functions(self, service, **kwargs):
        functions = {}
        for api in self.apis.values():
            function = api.function(service)
            if not function:
                continue

            functions[api.name.spinal] = function

        return functions

    @property
    def rest(self):
        return self.apis.get("rest")

    @property
    def appsync(self):
        return self.apis.get("appsync")

    @property
    def graphql(self):
        return self.apis.get("graphql")

    def create(self, name, type_):
        if name in self.apis:
            raise KeyError(f"There is already API named {name}")

        api = type_(self, name=name)
        self.apis[name] = api

        return api

    def configure(self, service_name=None, stage=None):
        if service_name:
            self.service_name = Identifier(service_name)

        if stage:
            self.stage = stage
