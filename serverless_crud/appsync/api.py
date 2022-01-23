from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.event_handler.appsync import Router

from serverless_crud.actions import GetAction, CreateAction, UpdateAction, DeleteAction, ListAction
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

    def registry(self, model, alias=None, get=GetAction, create=CreateAction, update=UpdateAction, delete=DeleteAction,
                 lookup_list=ListAction):
        super().registry(model, alias, get, create, update, delete, lookup_list, None, None)

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

        if create_callback:
            @router.resolver(type_name="Mutation", field_name=f"create{alias}")
            def create(input, *args, **kwargs):
                response, obj = create_callback(
                    payload=input, event=router.current_event, context=router.lambda_context
                )
                # if isinstance(obj, Response):
                #     return obj

                return

        if update_callback:
            @router.resolver(type_name="Mutation", field_name=f"update{alias}")
            def update(input, *args, **kwargs):
                response, obj = update_callback(router.current_event, router.lambda_context)

                # if isinstance(obj, Response):
                #     return obj

                # return JsonResponse(201, obj.dict())

                return

        if delete_callback:
            @router.resolver(type_name="Mutation", field_name=f"delete{alias}")
            def delete(*args, **kwargs):
                primary_key = PrimaryKey(**{k: model.cast_to_type(k, v) for k, v in kwargs.items()})
                response, obj = delete_callback(
                    *args, primary_key=primary_key, event=router.current_event, context=router.lambda_context
                )

                # if isinstance(obj, Response):
                #     return obj

                # return JsonResponse(200, {})

        if lookup_list_callback:
            @router.resolver(type_name="Query", field_name=f"list{alias}s")
            def lookup_list(index=None, *args, **kwargs):
                response, objs = lookup_list_callback(
                    index_name=index, event=router.current_event, context=router.lambda_context, *args, **kwargs
                )

                # if isinstance(objs, Response):
                #     return objs

                # return JsonResponse(200, [obj.dict() for obj in objs])

        self.app.include_router(router)
