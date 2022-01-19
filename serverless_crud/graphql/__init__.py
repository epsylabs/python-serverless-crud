from serverless_crud.service import API as BaseAPI


class API(BaseAPI):
    def handle(self, event, context):
        pass

    def registry(self, model, alias=None):
        pass
