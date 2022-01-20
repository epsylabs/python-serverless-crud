from aws_lambda_powertools.event_handler import ApiGatewayResolver, content_types
from aws_lambda_powertools.event_handler.api_gateway import Router, Response

from serverless_crud.actions import *
from serverless_crud.exceptions import APIException
from serverless_crud.rest.http import JsonResponse
from serverless_crud.service import API as BaseAPI


class PrimaryKey:
    def __init__(self, **kwargs):
        self._values = kwargs

    def raw(self):
        return self._values

    def __repr__(self):
        return str(self._values)


class API(BaseAPI):
    def __init__(self) -> None:
        super().__init__()
        self.models = []
        self.app = ApiGatewayResolver(strip_prefixes=[f"/rest"])

        @self.app.exception_handler(APIException)
        def handle_api_exception(ex: APIException):
            return ex.as_response()

        # @self.app.exception_handler(ValueError)
        # def handle_value_error(ex: ValueError):
        #     metadata = {"path": self.app.current_event.path}
        #
        #     return Response(
        #         status_code=400,
        #         content_type=content_types.APPLICATION_JSON,
        #         body='{"message": "Invalid request"}',
        #     )

    def registry(self, model, alias=None, get=GetAction, create=CreateAction, update=UpdateAction, delete=DeleteAction,
                 search=SearchAction):
        self.models.append(model)
        self._create_model_app(
            model, alias,
            get_callback=get(model) if get else None,
            create_callback=create(model) if create else None,
            update_callback=update(model) if update else None,
            delete_callback=delete(model) if delete else None,
            search_callback=search(model) if search else None
        )

    def handle(self, event, context):
        return self.app.resolve(event, context)

    def _create_model_app(self, model, alias, get_callback, create_callback, update_callback, delete_callback,
                          search_callback):
        router = Router()

        id_route_pattern = f"/{alias}/<{model._meta.key.partition_key}>"
        if len(model._meta.key.key_fields) > 1:
            id_route_pattern += f"/<{model._meta.key.sort_key}>"

        if get_callback:
            @router.get(id_route_pattern)
            def get(*args, **kwargs):
                primary_key = PrimaryKey(**{k: model.cast_to_type(k, v) for k, v in kwargs.items()})

                return get_callback(*args, primary_key=primary_key, event=router.current_event,
                                    context=router.lambda_context)

        if create_callback:
            @router.post(f"/{alias}")
            def create():
                response, obj = create_callback(router.current_event, router.lambda_context)
                if isinstance(obj, Response):
                    return obj

                return JsonResponse(201, obj.dict())

        if update_callback:
            @router.put(id_route_pattern)
            def update(*args, **kwargs):
                response, obj = update_callback(router.current_event, router.lambda_context)

                if isinstance(obj, Response):
                    return obj

                return JsonResponse(201, obj.dict())

        if delete_callback:
            @router.delete(id_route_pattern)
            def delete(*args, **kwargs):
                primary_key = PrimaryKey(**{k: model.cast_to_type(k, v) for k, v in kwargs.items()})
                response, obj = delete_callback(*args, primary_key=primary_key, event=router.current_event,
                                       context=router.lambda_context)

                if isinstance(obj, Response):
                    return obj

                return JsonResponse(200, {})

        if search_callback:
            @router.post(f"/lookup/{alias}")
            def search(*args, **kwargs):
                return search_callback(event=router.current_event, context=router.lambda_context, *args, **kwargs)

        self.app.include_router(router)
