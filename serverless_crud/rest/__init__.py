from aws_lambda_powertools.event_handler import ApiGatewayResolver
from aws_lambda_powertools.event_handler.api_gateway import Router, Response

from serverless_crud.actions import *
from serverless_crud.actions.search import ListAction, ScanAction, QueryAction
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

    def registry(self, model, alias=None, get=GetAction, create=CreateAction, update=UpdateAction, delete=DeleteAction,
                 lookup_list=ListAction, lookup_scan=ScanAction, lookup_query=QueryAction):
        self.models.append(model)
        self._create_model_app(
            model, alias,
            get_callback=get(model) if get else None,
            create_callback=create(model) if create else None,
            update_callback=update(model) if update else None,
            delete_callback=delete(model) if delete else None,
            lookup_list_callback=lookup_list(model) if lookup_list else None,
            lookup_scan_callback=lookup_scan(model) if lookup_scan else None,
            lookup_query_callback=lookup_query(model) if lookup_query else None,
        )

    def handle(self, event, context):
        return self.app.resolve(event, context)

    def _create_model_app(self, model, alias, get_callback, create_callback, update_callback, delete_callback,
                          lookup_list_callback, lookup_scan_callback, lookup_query_callback):
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
                response, obj = create_callback(payload=router.current_event.json_body, event=router.current_event, context=router.lambda_context)
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

        if lookup_list_callback:
            def lookup_list(index=None, *args, **kwargs):
                response, objs = lookup_list_callback(index_name=index, event=router.current_event,
                                                      context=router.lambda_context, *args, **kwargs)

                if isinstance(objs, Response):
                    return objs

                return JsonResponse(200, [obj.dict() for obj in objs])

            router.get(f"/lookup/{alias}/list/<index>")(lookup_list)
            router.get(f"/lookup/{alias}/list")(lookup_list)

        if lookup_scan_callback:
            def lookup_scan(*args, **kwargs):
                response, objs = lookup_scan_callback(event=router.current_event, context=router.lambda_context, *args,
                                                      **kwargs)

                if isinstance(objs, Response):
                    return objs

                return JsonResponse(200, [obj.dict() for obj in objs])

            router.post(f"/lookup/{alias}/scan/<index>")(lookup_scan)
            router.post(f"/lookup/{alias}/scan")(lookup_scan)

        if lookup_query_callback:
            def lookup_query(*args, **kwargs):
                response, objs = lookup_query_callback(event=router.current_event, context=router.lambda_context, *args,
                                                      **kwargs)

                if isinstance(objs, Response):
                    return objs

                return JsonResponse(200, [obj.dict() for obj in objs])

            router.post(f"/lookup/{alias}/query/<index>")(lookup_query)
            router.post(f"/lookup/{alias}/query")(lookup_query)

        self.app.include_router(router)
