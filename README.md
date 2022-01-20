# python-serverless-crud

## The idea 

Simple and powerful tool for quick serverless data management via API. 

## Key concepts

- Don't Repeat Yourself - easy model definition with schema and cloud formation generation support
- Best practices applied by default (created with AWS LambdaPower Tools)
- Flexibility - enable, extend and modify what is needed
- One ring to rule them all - support for REST API, GraphQL (via API Gateway), AppSync GraphQL (direct resolvers)


## Features

- Full CRUD support with validation
- Native support for DynamoDB (including CloudFormation creation via troposphere)
  - GlobalSecondaryIndex support
  - LocalSecondaryIndex support
  - Primary Key with and without sort keys
- Support for Scan, Query operations on the tables and indexes
- Virtual List method on the table or index
- Integrated record owner feature with KeyCondition and FilterCondition support (auto-detect)

# Documentation

## Sample service

```python
from aws_lambda_powertools import Tracer
from aws_lambda_powertools.logging import correlation_paths
from serverless_crud import api
from serverless_crud.dynamodb import annotation as db
from serverless_crud.model import BaseModel
from serverless_crud.logger import logger

tracer = Tracer()


@db.Model(
    key=db.PrimaryKey(id=db.KeyFieldTypes.HASH),
    indexes=(
            db.GlobalSecondaryIndex("by_user", user=db.KeyFieldTypes.HASH, created=db.KeyFieldTypes.RANGE),
    ),
    owner_field="user"
)
class Device(BaseModel):
    id: str
    created: int
    user: str = None


api.rest.registry(Device, alias="device")


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def rest_handler(event, context):
    return api.rest.handle(event, context)
```

With just a few lines of the code we are able to create `Device` model service which then can be extended. 
In this example we:

1. Defined our `Device` model with some extra metadata, used by our generators. That includes:
   1. Table key definition
   2. GlobalSecondaryIndex
   3. Definition of the field which will hold `owner` of the record (identity provided by cognito)
2. Registered our `Device` model into rest API under `device` alias
3. Created rest handler which then can be referred in our `serverless.yml` file 

A few notes here:
- we need to define `rest_handler` function if we would like to use it as a target for local execution with serverless freamework
- Lambda Power Tools are build around functions and they don't work properly with object methods
- We use one function per API type, and we relay on internal router provided by each API implementation 

### Serverless integration

If you use (serverless-builder)[https://github.com/epsyhealth/serverless-builder] you can create your `serverless.yml` with just a few lines of code (including DynamodbTables)

```python
from serverless import Service, Configuration
from serverless.aws.features import XRay
from serverless.aws.functions.http import HTTPFunction
from serverless.plugins import PythonRequirements, Prune
from serverless.provider import AWSProvider
from troposphere import dynamodb

from timemachine_api.handlers import api

service = Service(
    "timemachine-api",
    "Collect events in chronological order",
    AWSProvider(),
    config=Configuration(
        domain="epsy.app"
    )
)
service.provider.timeout = 5

service.plugins.add(Prune())
service.plugins.add(PythonRequirements(layer=False, useStaticCache=False, dockerSsh=True))

service.enable(XRay())

for name, table_specification in api.dynamodb_table_specifications().items():
    service.resources.add(dynamodb.Table(name, **table_specification))

authorizer = dict(name="auth",
                  arn="arn:aws:cognito-idp:us-east-1:772962929486:userpool/us-east-1_FCl7gKtHC")

service.builder.function.http("rest", "Time machine REST API", "/rest/{proxy+}", HTTPFunction.ANY,
                              handler="timemachine_api.handlers.rest_handler", authorizer=authorizer)


service.render()
```

## Internals

### Annotations

`serverless-crud` project provides one annotation which must be used for all managed models.

```python
from serverless_crud.dynamodb import annotation as db
@db.Model(
    key=db.PrimaryKey(name=db.KeyFieldTypes.HASH),
    indexes=(
        db.GlobalSecondaryIndex(...),
        db.LocalSecondaryIndex(...)
    ),
    owner_field="field"
)
```

Model annotation accepts:
- `key` - primary key definition, in form of `kwargs` where name of parameter would be a field name which should 
 be used  in key, and value should be a value of `KeyFieldTypes` enum
- `indexes` - list of indexes GlobalSecondaryIndex|LocalSecondaryIndex. Indexes are defined in same way as primary key
- `owner_field` - name of the field which should be used for data filtering (based on the cognito identity)


### Data owner 

`serverless-crud` can enforce some base data filtering on all kind of operations using Dynamodb conditional operations. 
If you would like to use this feature you must set `owner_field` on each model you would like to use this feature.

Library will use this field for:
- setting its value on model creation / update (it will overwrite any value provided by user)
- as an extra `ConditionExpression` during `GET` and `DELETE` operations
- as a part of either `FilterExpression` or `KeyExpression` for Scan, Query and List operations


### Model registration

To be able to manage given model, you must first register it with specific API. 
This can be done with a single line of code:

```python
api.rest.registry(Device, alias="device")
```

You need to provide only a model type to `registry` method, all other parameters are optional. 
If you like, you can omit `alias` parameter, in that case framework will use model class name.

### Customizing endpoint behaviour

Framework defines a set of classes located in `serverless_crud.actions`:
- CreateAction
- DeleteAction
- GetAction
- ScanAction, ListAction, QueryAction
- UpdateAction

all those classes are subclasses of `serverless_crud.actions.base.Action` class and can be extended if needed. 

You may need to execute custom logic after object creation, that can be done with custom `CreateAction` subclass
```python

from serverless_crud.actions import CreateAction

class CreateDeviceAction(CreateAction):
    def handle(self, event: APIGatewayProxyEvent, context):
        super().handle(event, context)
        
        # custom logic


api.rest.registry(Device, create=CreateDeviceAction)
```

You can set custom handlers for each supported operation:

```python
def registry(self, model, alias=None, get=GetAction, create=CreateAction, update=UpdateAction, delete=DeleteAction,
             lookup_list=ListAction, lookup_scan=ScanAction, lookup_query=QueryAction):
```

As you can see, all actions are defined by default. That also means that all actions are enabled by default, but
each action can be disabled.

If you need to disable action you need to set action handler to `None`, that will prevent framework from creating
route for given action, and it will disable whole logic behind it. 

### Routes

REST API specific feature. 

Framework will create multiple routes for each register model, using `alias` as a URL namespace. 
Generated routes: 

- GET /rest/{alias}/{pk} - fetch object by PK (see notes about PK below)
- POST /rest/{alias} - create new record
- PUT /rest/{alias}/{pk} - update record with given PK 
- DELETE /rest/{alias}/{pk} - delete record with given PK 
- GET /rest/lookup/{alias}/list - list all the records of given type using Query on the table
- GET /rest/lookup/{alias}/list/{index_name} - list all the records of the given type using Query on specific index
- POST /rest/lookup/{alias}/query - perform a query on given table
- POST /rest/lookup/{alias}/query/{index_name} - perform a query on given index
- POST /rest/lookup/{alias}/scan - perform a scan on given table
- POST /rest/lookup/{alias}/scan/{index_name} - perform a scan on given index

#### Primary Keys
> *Please remember that with DynamoDB key is a Partition Key with optional Sort Key. 
In case you define Sort Key DynamoDB will require a value for it while getting / deleting key.
In that case framework will modify routes to include sort key as an extra path parameter* 


## Endpoints
