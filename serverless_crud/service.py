import os

from serverless_crud.appsync import AppSyncAPI
from serverless_crud.graphql import GraphQLAPI
from serverless_crud.rest import RestAPI
from serverless_crud.utils import Identifier


class Manager:
    def __init__(self):
        self.rest = RestAPI(self)
        self.graphql = GraphQLAPI(self)
        self.appsync = AppSyncAPI(self)

        self.service_name = Identifier(os.getenv("SERVICE_NAME", "api"))
        self.stage = os.getenv("STAGE", "current")

    def resources(self, service=None):
        resources = []
        resources += self.rest.resources(service=service)
        resources += self.graphql.resources(service=service)
        resources += self.appsync.resources(service=service)

        return resources

    def functions(self, service, **kwargs):
        return {f.name.snake: f for f in filter(None, [self.rest.function(service), self.graphql.function(service), self.appsync.function(service)])}

    def configure(self, service_name=None, stage=None):
        if service_name:
            self.service_name = Identifier(service_name)

        if stage:
            self.stage = stage
