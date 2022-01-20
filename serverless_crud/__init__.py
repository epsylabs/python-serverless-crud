from serverless_crud.dynamodb.builder import model_to_table_specification
from serverless_crud.appsync import API as AppSyncApi
from serverless_crud.graphql import API as GraphQLApi
from serverless_crud.rest import API as RestApi


class Manager:
    def __init__(self):
        self.rest = RestApi()
        self.graphql = GraphQLApi()
        self.appsync = AppSyncApi()

    def dynamodb_table_specifications(self):
        tables = {}
        for model in self.rest.models:
            tables[model._meta.table_name] = model_to_table_specification(model)

        # for model in self.graphql.models:
        #     pass

        return tables


api = Manager()
