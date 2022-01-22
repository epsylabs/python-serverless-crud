from serverless_crud.api import BaseAPI


class GraphQLAPI(BaseAPI):
    def _create_model_app(self, model, alias, get_callback, create_callback, update_callback, delete_callback,
                          lookup_list_callback, lookup_scan_callback, lookup_query_callback):
        pass

    def handle(self, event, context):
        pass
