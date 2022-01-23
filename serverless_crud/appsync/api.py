from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.event_handler.appsync import Router

from serverless_crud.api import BaseAPI


class PrimaryKey:
    def __init__(self, **kwargs):
        self._values = kwargs

    def raw(self):
        return self._values

    def __repr__(self):
        return str(self._values)


class AppSyncAPI(BaseAPI):
    def __init__(self, manager) -> None:
        super().__init__(manager)
        self.app = AppSyncResolver()

    def handle(self, event, context):
        return self.app.resolve(event, context)

    def function(self, service, handler=None, **kwargs):
        if not self.models:
            return

        if self._function:
            return self._function

        handler = handler or f"{service.service.snake}.handlers.appsync_handler"

        self._function = service.builder.function.generic(
            "appsync",
            "AppSync API resolver",
            handler=handler,
            role=f"arn:aws:iam::${{aws:accountId}}:role/{self.iam_execution_role_name()}",
            **kwargs,
        )

        return self._function

    def _create_model_app(
        self,
        model,
        alias,
        get_callback,
        create_callback,
        update_callback,
        delete_callback,
        lookup_list_callback,
        lookup_scan_callback,
        lookup_query_callback,
    ):
        router = Router()

        if get_callback:

            @router.resolver(type_name="Query", field_name=f"get{alias}")
            def get(*args, **kwargs):
                primary_key = PrimaryKey(**{k: model.cast_to_type(k, v) for k, v in kwargs.items()})

                return get_callback(
                    *args, primary_key=primary_key, event=router.current_event, context=router.lambda_context
                )

        # if create_callback:
        #     @router.resolver(type_name="Mutation", field_name=f"create{alias}")
        #     def create():
        #         response, obj = create_callback(router.current_event, router.lambda_context)
        #         # if isinstance(obj, Response):
        #         #     return obj
        #
        #         return JsonResponse(201, obj.dict())
        #
        # if update_callback:
        #     @router.put(id_route_pattern)
        #     def update(*args, **kwargs):
        #         response, obj = update_callback(router.current_event, router.lambda_context)
        #
        #         if isinstance(obj, Response):
        #             return obj
        #
        #         return JsonResponse(201, obj.dict())
        #
        # if delete_callback:
        #     @router.delete(id_route_pattern)
        #     def delete(*args, **kwargs):
        #         primary_key = PrimaryKey(**{k: model.cast_to_type(k, v) for k, v in kwargs.items()})
        #         response, obj = delete_callback(*args, primary_key=primary_key, event=router.current_event,
        #                                         context=router.lambda_context)
        #
        #         if isinstance(obj, Response):
        #             return obj
        #
        #         return JsonResponse(200, {})

        # if lookup_list_callback:
        #     def lookup_list(index=None, *args, **kwargs):
        #         response, objs = lookup_list_callback(index_name=index, event=router.current_event,
        #                                               context=router.lambda_context, *args, **kwargs)
        #
        #         # if isinstance(objs, Response):
        #         #     return objs
        #
        #         return JsonResponse(200, [obj.dict() for obj in objs])
        #
        #     router.resolver(type_name="Query", field_name=f"list{alias}s")(lookup_list)
        # router.get(f"/lookup/{alias}/list")(lookup_list)

        # if lookup_scan_callback:
        #     def lookup_scan(*args, **kwargs):
        #         response, objs = lookup_scan_callback(event=router.current_event, context=router.lambda_context, *args,
        #                                               **kwargs)
        #
        #         if isinstance(objs, Response):
        #             return objs
        #
        #         return JsonResponse(200, [obj.dict() for obj in objs])
        #
        #     router.post(f"/lookup/{alias}/scan/<index>")(lookup_scan)
        #     router.post(f"/lookup/{alias}/scan")(lookup_scan)
        #
        # if lookup_query_callback:
        #     def lookup_query(*args, **kwargs):
        #         response, objs = lookup_query_callback(event=router.current_event, context=router.lambda_context, *args,
        #                                                **kwargs)
        #
        #         if isinstance(objs, Response):
        #             return objs
        #
        #         return JsonResponse(200, [obj.dict() for obj in objs])
        #
        #     router.post(f"/lookup/{alias}/query/<index>")(lookup_query)
        #     router.post(f"/lookup/{alias}/query")(lookup_query)

        self.app.include_router(router)
