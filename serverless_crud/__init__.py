from serverless_crud.appsync import API as AppSyncApi
from serverless_crud.graphql import API as GraphQLApi
from serverless_crud.rest import API as RestApi


class Manager:
    def __init__(self):
        self.rest = RestApi()
        self.graphql = GraphQLApi()
        self.appsync = AppSyncApi()

    def resources(self):
        resources = []
        resources += self.rest.resources()
        resources += self.graphql.resources()
        resources += self.appsync.resources()

        return resources


api = Manager()
