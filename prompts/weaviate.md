### Install Weaviate Python Client

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/index.md

Install the Weaviate Python client using pip. This is the standard installation for basic usage.

```bash
pip install -U weaviate-client
```

--------------------------------

### Install Weaviate Python Client with Agent Support

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/index.md

Install the Weaviate Python client with optional agent support using the `[agents]` extra. This enables integration with Weaviate Agents for LLM-related tasks.

```bash
pip install -U "weaviate-client[agents]"
```

--------------------------------

### gRPC Configuration Example

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.classes.md

Example of how to configure gRPC channel options and credentials for the Weaviate client.

```python
from grpc import ssl_channel_credentials
import weaviate.classes as wvc

conf = wvc.init.GrpcConfig(
  channel_options=[
    ("grpc.keepalive_time_ms", 10000),
    ("grpc.keepalive_timeout_ms", 5000),
  ],
  credentials=ssl_channel_credentials(openssl_cafile=None, ssl_context=None, key_file=None, cert_file=None)

)
```

--------------------------------

### Pre-build hook for cloning and installing the agents client

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/PUBLISHING.md

This YAML snippet shows how the weaviate-agents-python-client is cloned and installed as a pre-build step in Read the Docs.

```yaml
build:
  jobs:
    pre_build:
      - git clone -b main --depth=1 https://github.com/weaviate/weaviate-agents-python-client.git docs/weaviate-agents-python-client
      - python -m pip install -e ./docs/weaviate-agents-python-client
```

--------------------------------

### Initialize BM25 Query and Generate Classes

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.queries.bm25.md

Example demonstrating the constructor signature for the internal BM25 query and generation classes. These classes require a connection object, collection name, and optional configuration for consistency, multi-tenancy, and data mapping.

```python
from weaviate.collections.queries.bm25 import _BM25Query, _BM25Generate

# Example instantiation pattern for internal BM25 classes
query_instance = _BM25Query(
    connection=connection,
    name="MyCollection",
    consistency_level=None,
    tenant=None,
    properties=None,
    references=None,
    validate_arguments=True
)

generate_instance = _BM25Generate(
    connection=connection,
    name="MyCollection",
    consistency_level=None,
    tenant=None,
    properties=None,
    references=None,
    validate_arguments=True
)
```

--------------------------------

### Manage Embedded Database Lifecycle

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Demonstrates how to initialize and control the lifecycle of an embedded Weaviate database instance using the EmbeddedV3 or EmbeddedV4 classes. Methods include checking connectivity and starting the service.

```python
from weaviate.embedded import EmbeddedV4, EmbeddedOptions

options = EmbeddedOptions(port=8079)
embedded_db = EmbeddedV4(options=options)

if not embedded_db.is_listening():
    embedded_db.start()
```

--------------------------------

### CrossReferenceAnnotation Example

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.classes.md

Example demonstrating how to use CrossReferenceAnnotation to include vectors and metadata when querying cross-referenced objects.

```python
>>> import typing
>>> import weaviate.classes as wvc
>>> 
>>> class One(typing.TypedDict):
...     prop: str
>>> 
>>> class Two(typing.TypedDict):
...     one: typing.Annotated[
...         wvc.CrossReference[One],
...         wvc.CrossReferenceAnnotation(include_vector=True)
...     ]
```

--------------------------------

### Async Batch Wrapper Get Shards Readiness

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.batch.md

Internal method to get shard readiness status asynchronously.

```APIDOC
## async _BatchWrapperAsync__get_shards_readiness

### Description
Internal method to get shard readiness status asynchronously.

### Method
ASYNC

### Parameters
#### Path Parameters
- **shard** (Shard) - Required - The shard to check the status of.

### Return type
List[bool]
```

--------------------------------

### Create Weaviate Collection from Dictionary (Async)

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.collections.md

Create a new collection in Weaviate using a configuration dictionary and immediately get a collection object. This is useful for v3 to v4 migrations and experimental features. Requires a successful connection to Weaviate.

```python
from weaviate.collections.collection import CollectionAsync

# Assuming 'connection_async' is an initialized ConnectionAsync object
collections_async = _CollectionsAsync(connection_async)

collection_config_dict = {
    "class": "MyNewCollection",
    "description": "A new collection created from a dictionary",
    "properties": [
        {
            "name": "title",
            "dataType": ["text"]
        }
    ]
}

# The return type is CollectionAsync, but without generic types specified here
new_collection: CollectionAsync = await collections_async.create_from_dict(config=collection_config_dict)
```

--------------------------------

### CrossReference Type Hint Example

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.classes.md

Example of how to use CrossReference for type hinting within a generic data model.

```python
>>> import typing
>>> import weaviate.classes as wvc
>>> 
>>> class One(typing.TypedDict):
...     prop: str
>>> 
>>> class Two(typing.TypedDict):
...     one: wvc.CrossReference[One]
```

--------------------------------

### GET /v1/meta

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/modules.md

Retrieves the metadata of the Weaviate instance, including version and module information.

```APIDOC
## GET /v1/meta

### Description
Retrieves the metadata of the connected Weaviate instance to verify versioning and enabled modules.

### Method
GET

### Endpoint
/v1/meta

### Parameters
None

### Request Example
GET /v1/meta

### Response
#### Success Response (200)
- **version** (string) - The version of the Weaviate instance.
- **modules** (object) - A dictionary of enabled modules and their configurations.

#### Response Example
{
  "version": "1.24.0",
  "modules": {
    "text2vec-openai": {}
  }
}
```

--------------------------------

### Create Weaviate Collection from Config Object (Async)

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.collections.md

Create a new collection in Weaviate using a pre-defined configuration object and immediately get a collection object. This method is suitable for creating collections with complex configurations. Requires a successful connection to Weaviate.

```python
from weaviate.collections.classes.config import CollectionConfig, Property, DataType
from weaviate.collections.collection import CollectionAsync

# Assuming 'connection_async' is an initialized ConnectionAsync object
collections_async = _CollectionsAsync(connection_async)

collection_config_obj = CollectionConfig(
    name="MyNewCollectionFromConfig",
    description="A new collection created from a config object",
    properties=[
        Property(name="content", dataType=[DataType.TEXT])
    ]
)

# The return type is CollectionAsync, but without generic types specified here
new_collection: CollectionAsync = await collections_async.create_from_config(config=collection_config_obj)
```

--------------------------------

### Async Replication Configuration

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.classes.md

Example of creating a configuration object for async replication settings when creating a collection. This feature requires WeaviateDB version 1.36.0 or later.

```python
from weaviate.collections.classes.config import _Replication

# Example usage (assuming this is part of a larger collection creation process)
replication_config = _Replication.async_config(
    max_workers=4,
    hashtree_height=10,
    frequency=60,
    frequency_while_propagating=30,
    alive_nodes_checking_frequency=10,
    logging_frequency=5,
    diff_batch_size=100,
    diff_per_node_timeout=10,
    pre_propagation_timeout=5,
    propagation_timeout=60,
    propagation_limit=1000,
    propagation_delay=0.1,
    propagation_batch_size=50,
    propagation_concurrency=2
)
```

--------------------------------

### GET /v1/nodes

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/modules.md

Checks the status and readiness of the Weaviate cluster nodes.

```APIDOC
## GET /v1/nodes

### Description
Returns the status of the nodes in the cluster, indicating if they are ready to accept requests.

### Method
GET

### Endpoint
/v1/nodes

### Parameters
None

### Request Example
GET /v1/nodes

### Response
#### Success Response (200)
- **nodes** (array) - List of node status objects.

#### Response Example
{
  "nodes": [
    {
      "name": "node-1",
      "status": "HEALTHY"
    }
  ]
}
```

--------------------------------

### GET /v1/objects (Fetch Objects)

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.queries.fetch_objects.md

The FetchObjects query interface allows users to retrieve objects from a specific collection with support for synchronous and asynchronous execution.

```APIDOC
## GET /v1/objects

### Description
Retrieves objects from a Weaviate collection based on specified properties and references. Supports both synchronous and asynchronous execution modes.

### Method
GET

### Endpoint
/v1/objects

### Parameters
#### Path Parameters
- **name** (str) - Required - The name of the collection to query.

#### Query Parameters
- **consistency_level** (ConsistencyLevel) - Optional - The consistency level for the read operation.
- **tenant** (str) - Optional - The tenant name for multi-tenancy support.

#### Request Body
- **properties** (Mapping) - Optional - The properties to retrieve for each object.
- **references** (Mapping) - Optional - The references to resolve for each object.
- **validate_arguments** (bool) - Optional - Whether to validate the query arguments before execution.

### Request Example
{
  "name": "Article",
  "properties": {"title": null, "wordCount": null},
  "consistency_level": "ONE"
}

### Response
#### Success Response (200)
- **objects** (List) - A list of objects matching the query criteria.

#### Response Example
{
  "objects": [
    {
      "class": "Article",
      "properties": {"title": "Weaviate Guide", "wordCount": 1500}
    }
  ]
}
```

--------------------------------

### Get Failed References

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.batch.md

Retrieves a list of all references that failed during the batch import process.

```APIDOC
## property failed_references

### Description
Get all failed references from the batch manager.

### Returns
A list of all the failed references from the batch.

### Return type
List[ErrorReference]
```

--------------------------------

### Get Shard Readiness Status

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.batch.md

Asynchronously checks the readiness status of a given shard.

```APIDOC
## async _get_shards_readiness

### Description
Checks the readiness status of a given shard.

### Method
ASYNC

### Parameters
#### Path Parameters
- **shard** (Shard) - Required - The shard to check the status of.

### Return type
List[bool]
```

--------------------------------

### Get Failed Objects

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.batch.md

Retrieves a list of all objects that failed during the batch import process.

```APIDOC
## property failed_objects

### Description
Get all failed objects from the batch manager.

### Returns
A list of all the failed objects from the batch.

### Return type
List[ErrorObject]
```

--------------------------------

### Get Batch Results

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.batch.md

Retrieves the overall results of the batch operation.

```APIDOC
## property results

### Description
Get the results of the batch operation.

### Returns
The results of the batch operation.

### Return type
BatchResult
```

--------------------------------

### GET number_errors

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.batch.md

Retrieves the count of errors encountered in the current batch.

```APIDOC
## GET number_errors

### Description
Get the number of errors in the current batch.

### Response
- **Returns** (int) - The number of errors in the current batch.
```

--------------------------------

### GET /batch/errors

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.batch.md

Retrieves the count of errors encountered in the current batch.

```APIDOC
## GET /batch/errors

### Description
Get the number of errors in the current batch.

### Response
#### Success Response (200)
- **count** (int) - The number of errors in the current batch.
```

--------------------------------

### GET /v1/objects (Fetch by IDs)

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.queries.fetch_objects_by_ids.md

Retrieves specific objects from a Weaviate collection using their IDs. This endpoint supports both synchronous and asynchronous execution patterns.

```APIDOC
## GET /v1/objects

### Description
Retrieves objects from a specific collection by providing their unique IDs. This query supports specifying properties and references to be returned.

### Method
GET

### Endpoint
/v1/objects

### Parameters
#### Query Parameters
- **ids** (array) - Required - List of UUIDs to fetch.
- **collection** (string) - Required - The name of the collection.
- **consistency_level** (string) - Optional - The consistency level for the read operation.
- **tenant** (string) - Optional - The tenant name for multi-tenancy collections.

### Request Example
{
  "ids": ["uuid1", "uuid2"],
  "collection": "MyCollection"
}

### Response
#### Success Response (200)
- **objects** (array) - List of retrieved objects.

#### Response Example
{
  "objects": [
    {
      "id": "uuid1",
      "properties": { "name": "example" }
    }
  ]
}
```

--------------------------------

### Get Number of Errors in Batch

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.batch.md

Retrieves the number of errors encountered in the current batch.

```APIDOC
## GET /batch/errors/count

### Description
Retrieves the number of errors encountered in the current batch.

### Method
GET

### Endpoint
/batch/errors/count

### Parameters
#### Path Parameters
None

#### Query Parameters
None

#### Request Body
None

### Request Example
```json
{} 
```

### Response
#### Success Response (200)
- **count** (int) - The number of errors in the current batch.

#### Response Example
```json
{
  "count": 0
}
```
```

--------------------------------

### Initialize and Connect to Local Weaviate Async Client

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Demonstrates how to initialize a local Weaviate async client. It shows both the manual approach using connect/close methods and the recommended approach using an async context manager for automatic resource cleanup.

```python
import weaviate

# Without Context Manager
client = weaviate.use_async_with_local(
    host="localhost",
    port=8080,
    grpc_port=50051,
)
await client.connect()
# ... perform operations ...
await client.close()

# With Context Manager
async with weaviate.use_async_with_local(
    host="localhost",
    port=8080,
    grpc_port=50051,
) as client:
    is_ready = await client.is_ready()
    print(is_ready)
```

--------------------------------

### Initialize and Connect to Embedded Weaviate Async Client

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Demonstrates how to initialize an embedded async client, connect to it, and verify readiness. It also shows the recommended approach using an async context manager for automatic resource cleanup.

```python
import weaviate

# Manual connection management
client = weaviate.use_async_with_embedded(
    port=8080,
    grpc_port=50051
)
await client.connect()
ready = await client.is_ready()

# Using context manager for automatic cleanup
async with weaviate.use_async_with_embedded(
    port=8080,
    grpc_port=50051
) as client:
    ready = await client.is_ready()
```

--------------------------------

### Get Collection Object

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.collections.md

This method retrieves a collection object that can be used for interacting with your Weaviate collection. It does not send a request to Weaviate but rather creates a Python object for subsequent operations.

```APIDOC
## GET /weaviate/weaviate-python-client

### Description
Retrieves a collection object for interacting with a specified Weaviate collection. This method prepares a Python object for use in subsequent operations and does not directly communicate with the Weaviate instance.

### Method
GET (Conceptual - this is a client-side method)

### Endpoint
N/A (Client-side method)

### Parameters
#### Path Parameters
None

#### Query Parameters
None

#### Request Body
None

### Request Example
```python
# Assuming 'client' is an initialized Weaviate client instance
collection = client.get_collection(name="my_collection")
```

### Response
#### Success Response (200)
Returns a collection object (e.g., `Collection` or `CollectionAsync`) that allows for further interaction with the specified Weaviate collection.

#### Response Example
```python
# Conceptual representation of the returned object
<WeaviateCollectionObject>
```

### Exceptions
- **WeaviateInvalidInputError**: Raised if the input parameters are invalid.
- **InvalidDataModelException**: Raised if the provided data model is not a valid dictionary or TypedDict.
```

--------------------------------

### GET /collections/{name}/objects/{id}

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.queries.fetch_object_by_id.md

Retrieves a single object from a specified collection by its unique ID, allowing for configuration of consistency levels, tenant scoping, and property selection.

```APIDOC
## GET /collections/{name}/objects/{id}

### Description
Fetches a specific object from a Weaviate collection using its UUID. Supports optional parameters for consistency, multi-tenancy, and specific property projection.

### Method
GET

### Endpoint
/collections/{name}/objects/{id}

### Parameters
#### Path Parameters
- **name** (str) - Required - The name of the collection.
- **id** (str) - Required - The UUID of the object.

#### Query Parameters
- **consistency_level** (ConsistencyLevel) - Optional - The consistency level for the read operation.
- **tenant** (str) - Optional - The tenant name for multi-tenant collections.

### Request Example
GET /collections/MyCollection/objects/5b69097f-1da3-4a2a-8d3e-f7614d345c2a

### Response
#### Success Response (200)
- **object** (dict) - The requested object data including properties and references.

#### Response Example
{
  "id": "5b69097f-1da3-4a2a-8d3e-f7614d345c2a",
  "properties": {
    "name": "example_object",
    "value": 42
  }
}
```

--------------------------------

### Initialize Collection Configuration Classes

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.config.md

Demonstrates the instantiation of synchronous and asynchronous configuration objects for a Weaviate collection. These classes require a connection object and the collection name, with an optional tenant identifier.

```python
from weaviate.collections.config import _ConfigCollection, _ConfigCollectionAsync

# Synchronous configuration access
sync_config = _ConfigCollection(connection=conn, name="MyCollection", tenant="tenant_a")

# Asynchronous configuration access
async_config = _ConfigCollectionAsync(connection=conn, name="MyCollection", tenant="tenant_a")
```

--------------------------------

### Initialize Collection Backup Classes

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.backups.md

Demonstrates how to instantiate the synchronous and asynchronous backup handlers. These classes require a connection object and the name of the backup to operate.

```python
from weaviate.collections.backups import _CollectionBackup, _CollectionBackupAsync

# Synchronous initialization
sync_backup = _CollectionBackup(connection=my_connection, name="backup_name")

# Asynchronous initialization
async_backup = _CollectionBackupAsync(connection=my_connection, name="backup_name")
```

--------------------------------

### Connect to Embedded Weaviate Instance

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Demonstrates how to initialize an embedded Weaviate client using standard connection parameters. It shows both manual connection management and the recommended context manager pattern to ensure resources are properly released.

```python
import weaviate

# Manual connection management
client = weaviate.connect_to_embedded(
    port=8080,
    grpc_port=50051,
)
print(client.is_ready())
client.close()

# Using a context manager for automatic resource cleanup
with weaviate.connect_to_embedded(
    port=8080,
    grpc_port=50051,
) as client:
    print(client.is_ready())
```

--------------------------------

### Build HTML Documentation Locally

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/README.rst

Commands to build the HTML documentation locally from the 'docs' directory and open the generated index file.

```bash
make html
```

```bash
open _build/html/index.html
```

--------------------------------

### Connect to Weaviate Cloud Instance

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Demonstrates how to initialize a connection to a Weaviate Cloud cluster using API key authentication. It shows both the manual approach requiring a close() call and the recommended context manager pattern.

```python
import weaviate

# Manual connection management
client = weaviate.connect_to_weaviate_cloud(
    cluster_url="rAnD0mD1g1t5.something.weaviate.cloud",
    auth_credentials=weaviate.classes.init.Auth.api_key("my-api-key"),
)
client.is_ready()
client.close()

# Using context manager for automatic cleanup
with weaviate.connect_to_weaviate_cloud(
    cluster_url="rAnD0mD1g1t5.something.weaviate.cloud",
    auth_credentials=weaviate.classes.init.Auth.api_key("my-api-key"),
) as client:
    client.is_ready()
```

--------------------------------

### Connect to a local Weaviate instance

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Demonstrates how to connect to a local Weaviate instance using the Python client. It shows both the manual approach requiring a call to .close() and the recommended context manager approach for automatic resource management.

```python
import weaviate

# Approach 1: Manual connection management
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    grpc_port=50051
)
client.is_ready()
client.close()

# Approach 2: Using a context manager (Recommended)
with weaviate.connect_to_local(
    host="localhost",
    port=8080,
    grpc_port=50051
) as client:
    client.is_ready()
```

--------------------------------

### Initialize Near Image Query Classes

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.queries.near_image.md

Demonstrates the instantiation of the internal _NearImageQuery and _NearImageGenerate classes. These classes require a connection object, collection name, and optional configuration for consistency, multi-tenancy, and property mapping.

```python
from weaviate.collections.queries.near_image import _NearImageQuery, _NearImageGenerate

# Example instantiation of the query class
near_image_query = _NearImageQuery(
    connection=connection,
    name="MyCollection",
    consistency_level=None,
    tenant=None,
    properties=None,
    references=None,
    validate_arguments=True
)

# Example instantiation of the generative query class
near_image_gen = _NearImageGenerate(
    connection=connection,
    name="MyCollection",
    consistency_level=None,
    tenant=None,
    properties=None,
    references=None,
    validate_arguments=True
)
```

--------------------------------

### Create Async Weaviate Client with Custom Parameters (Python)

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

This snippet demonstrates how to initialize an asynchronous Weaviate client with specific HTTP and gRPC connection details. It shows both manual connection management (connect/close) and the preferred method using an async context manager for automatic connection handling.

```python
import weaviate

# Without Context Manager
client = weaviate.use_async_with_custom(
    http_host="localhost",
    http_port=8080,
    http_secure=False,
    grpc_host="localhost",
    grpc_port=50051,
    grpc_secure=False,
)
# Manual connection and closing
# await client.connect()
# await client.is_ready()
# await client.close()

# With Async Context Manager
async with weaviate.use_async_with_custom(
    http_host="localhost",
    http_port=8080,
    http_secure=False,
    grpc_host="localhost",
    grpc_port=50051,
    grpc_secure=False,
) as client:
    await client.is_ready()
# Connection is automatically closed here
```

--------------------------------

### weaviate.use_async_with_custom

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Initializes an asynchronous Weaviate client with specific host, port, and security configurations.

```APIDOC
## METHOD weaviate.use_async_with_custom

### Description
Creates an async client object ready to connect to a Weaviate instance with custom connection parameters. This method is useful for custom infrastructure setups where standard connection helpers are insufficient.

### Parameters
- **http_host** (str) - Required - The host for REST and GraphQL API calls.
- **http_port** (int) - Required - The port for REST and GraphQL API calls.
- **http_secure** (bool) - Required - Whether to use https.
- **grpc_host** (str) - Required - The host for the gRPC API.
- **grpc_port** (int) - Required - The port for the gRPC API.
- **grpc_secure** (bool) - Required - Whether to use a secure gRPC channel.
- **headers** (Dict[str, str]) - Optional - Additional request headers.
- **additional_config** (AdditionalConfig) - Optional - Advanced configuration options.
- **auth_credentials** (Auth) - Optional - Authentication credentials (API Key, Bearer Token, etc.).
- **skip_init_checks** (bool) - Optional - Whether to skip initialization checks.

### Request Example
```python
import weaviate
client = weaviate.use_async_with_custom(
    http_host="localhost",
    http_port=8080,
    http_secure=False,
    grpc_host="localhost",
    grpc_port=50051,
    grpc_secure=False
)
await client.connect()
```

### Response
- **Returns** (WeaviateAsyncClient) - An instance of the WeaviateAsyncClient ready for connection.
```

--------------------------------

### Configure gRPC Channel Settings

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Demonstrates how to initialize a GrpcConfig object with custom channel options and SSL credentials for secure gRPC communication.

```python
from grpc import ssl_channel_credentials
import weaviate.classes as wvc

conf = wvc.init.GrpcConfig(
    channel_options=[
        ("grpc.keepalive_time_ms", 10000),
        ("grpc.keepalive_timeout_ms", 5000),
    ],
    credentials=ssl_channel_credentials()
)
```

--------------------------------

### Initialize Weaviate Client

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

How to instantiate the main WeaviateClient object to interact with a Weaviate instance.

```APIDOC
## Initialization: WeaviateClient

### Description
The WeaviateClient is the main entry point for the v4 Python-native client. It encapsulates all functionalities and connects to a specific Weaviate instance.

### Constructor
`weaviate.WeaviateClient(connection_params=None, embedded_options=None, auth_client_secret=None, additional_headers=None, additional_config=None, skip_init_checks=False)`

### Parameters
- **connection_params** (dict) - Optional - Connection settings for the Weaviate instance.
- **auth_client_secret** (object) - Optional - Authentication credentials.
- **additional_headers** (dict) - Optional - Custom headers to include in requests.

### Usage Example
```python
import weaviate
client = weaviate.WeaviateClient(connection_params=weaviate.connect_to_local())
```
```

--------------------------------

### Create Async Weaviate Cloud Client (Python)

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Initializes an asynchronous client for Weaviate Cloud. Requires manual connection and closing, or can be used as an async context manager. Handles authentication and cluster connection details.

```python
import weaviate

# Without Context Manager
client = weaviate.use_async_with_weaviate_cloud(
    cluster_url="rAnD0mD1g1t5.something.weaviate.cloud",
    auth_credentials=weaviate.classes.init.Auth.api_key("my-api-key"),
)
await client.connect()
# Use client...
await client.close()

# With Context Manager
async with weaviate.use_async_with_weaviate_cloud(
    cluster_url="rAnD0mD1g1t5.something.weaviate.cloud",
    auth_credentials=weaviate.classes.init.Auth.api_key("my-api-key"),
) as client:
    # Use client...
    pass
```

--------------------------------

### Initialize Near Media Generation (Async)

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.queries.near_media.md

Initializes an asynchronous object for generating near media queries. It requires connection details, collection name, and optional parameters like consistency level, tenant, properties to search, references, and argument validation.

```python
from weaviate.collections.queries.near_media import _NearMediaGenerateAsync

# Assuming 'connection', 'name', 'properties', 'references' are defined
# near_media_generate_async = _NearMediaGenerateAsync(connection=connection, name=name, consistency_level=None, tenant=None, properties=properties, references=references, validate_arguments=True)
```

--------------------------------

### Initialize Near Text Query Classes

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.queries.near_text.md

Demonstrates the constructor signature for the internal _NearTextQueryAsync and _NearTextGenerateAsync classes used for asynchronous near-text operations.

```python
from weaviate.collections.queries.near_text import _NearTextQueryAsync, _NearTextGenerateAsync

# Example instantiation pattern for internal query classes
query_instance = _NearTextQueryAsync(
    connection=connection,
    name="my_collection",
    consistency_level=None,
    tenant=None,
    properties=None,
    references=None,
    validate_arguments=True
)
```

--------------------------------

### weaviate.use_async_with_local

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Initializes an asynchronous client for a local Weaviate instance.

```APIDOC
## FUNCTION weaviate.use_async_with_local

### Description
Creates an async client object ready to connect to a local Weaviate instance. This method supports manual connection management or usage as an async context manager.

### Parameters
- **host** (str) - Optional - The host to use for REST and GraphQL API calls (default: 'localhost').
- **port** (int) - Optional - The port to use for REST and GraphQL API calls (default: 8080).
- **grpc_port** (int) - Optional - The port to use for gRPC API (default: 50051).
- **headers** (Dict[str, str]) - Optional - Additional headers for requests.
- **additional_config** (AdditionalConfig) - Optional - Advanced configuration options.
- **skip_init_checks** (bool) - Optional - Whether to skip initialization checks.
- **auth_credentials** (Auth) - Optional - Authentication credentials (API key, bearer token, etc.).

### Returns
- **WeaviateAsyncClient** - The initialized async client instance.

### Usage Example
```python
import weaviate

# Using as a context manager
async with weaviate.use_async_with_local(
    host="localhost",
    port=8080,
    grpc_port=50051
) as client:
    is_ready = await client.is_ready()
```
```

--------------------------------

### Initialize Near Media Query (Async)

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.queries.near_media.md

Initializes an asynchronous object for executing near media queries. It takes connection information, collection name, and parameters for consistency level, tenant, properties, references, and argument validation.

```python
from weaviate.collections.queries.near_media import _NearMediaQueryAsync

# Assuming 'connection', 'name', 'properties', 'references' are defined
# near_media_query_async = _NearMediaQueryAsync(connection=connection, name=name, consistency_level=None, tenant=None, properties=properties, references=references, validate_arguments=True)
```

--------------------------------

### Create a Weaviate Collection from Configuration

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.collections.md

These methods create a new collection in the Weaviate instance and return the corresponding collection object. create_from_config uses a formal configuration object, while create_from_dict accepts a dictionary, useful for migrations or experimental features.

```python
collection = await client.collections.create_from_config(config_object)
# Or using a dictionary
collection = await client.collections.create_from_dict(config_dict)
```

--------------------------------

### Weaviate Backup Configuration for Creation

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.backup.md

Defines the configuration options for creating a new backup. It allows setting CPU percentage, chunk size, and compression level. This model inherits from a base configuration class.

```python
class BackupConfigCreate(_BackupConfigBase):
    cpu_percentage: int | None = None
    chunk_size: int | None = None
    compression_level: BackupCompressionLevel | None = None
```

--------------------------------

### Create Collection from Configuration

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.collections.md

Creates a Weaviate collection using a pre-defined configuration object and returns a collection object.

```APIDOC
## POST /weaviate/collections/create_from_config

### Description
Creates a collection in Weaviate using a pre-defined configuration object and returns a collection object.

### Method
POST

### Endpoint
/weaviate/collections/create_from_config

### Parameters
#### Request Body
- **config** (_CollectionConfig_) - Required - The collection’s configuration object.

### Request Example
```json
{
  "config": {
    "name": "MyCollection",
    "properties": [
      {
        "name": "title",
        "dataType": ["text"]
      }
    ]
  }
}
```

### Response
#### Success Response (200)
- **Collection** (*Collection*) - The created collection object.

#### Response Example
```json
{
  "collection": {
    "name": "MyCollection"
  }
}
```

### Errors
- **WeaviateConnectionError**: If the network connection to Weaviate fails.
- **UnexpectedStatusCodeError**: If Weaviate reports a non-OK status.
```

--------------------------------

### Initialize Near Vector Query Classes

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.queries.near_vector.md

Demonstrates the initialization of the _NearVectorQuery and _NearVectorGenerate classes. These classes require a connection object and configuration parameters to execute vector-based queries against a Weaviate collection.

```python
from weaviate.collections.queries.near_vector import _NearVectorQuery, _NearVectorGenerate

# Example initialization of a query executor
query_executor = _NearVectorQuery(
    connection=connection,
    name="my_collection",
    consistency_level=None,
    tenant=None,
    properties=None,
    references=None,
    validate_arguments=True
)
```

--------------------------------

### Method: create_from_config

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.collections.md

Creates a new collection in Weaviate using a configuration object.

```APIDOC
## create_from_config(config)

### Description
Creates a collection in Weaviate and returns the collection object using a predefined configuration object.

### Parameters
- **config** (_CollectionConfig) - Required - The collection configuration object.

### Response
- **Returns** (Collection) - The created collection object.
```

--------------------------------

### Create GitHub Release using GH CLI

Source: https://github.com/weaviate/weaviate-python-client/blob/main/RELEASING.md

This command uses the GitHub CLI to create a new release tag for the project. Replace `<VERSION_TAG>` with the desired semantic version (e.g., v4.18.1). This is a quick way to initiate a release.

```bash
gh release create <VERSION_TAG>
```

--------------------------------

### WeaviateAsyncClient Initialization

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Initializes an asynchronous Weaviate client instance with various connection and authentication options.

```APIDOC
## WeaviateAsyncClient Initialization

### Description
Initializes an asynchronous Weaviate client instance for interacting with a Weaviate server. Supports various connection parameters, embedded options, authentication methods, and additional headers.

### Parameters

* **connection_params** (*ConnectionParams* | None) – Connection parameters for HTTP requests.
* **embedded_options** (*EmbeddedOptions* | None) – Options for provisioning an embedded Weaviate instance.
* **auth_client_secret** (*_BearerToken* | *_ClientPassword* | *_ClientCredentials* | *_APIKey* | None) – Authentication modes (BearerToken, ClientPassword, ClientCredentials, APIKey).
* **additional_headers** (*dict* | None) – Additional headers for requests (e.g., API keys for modules).
* **additional_config** (*AdditionalConfig* | None) – Advanced configuration options.
* **skip_init_checks** (*bool*) – If True, skips initial Weaviate connection checks (useful for air-gapped environments).
```

--------------------------------

### Additional Client Configuration

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Configure connection, proxies, timeouts, and gRPC settings for the Weaviate client.

```APIDOC
## Additional Client Configuration

### Description
Use this class to specify additional connection and proxy settings for your client when connecting to Weaviate. It allows configuring connection details, proxies, timeouts, and gRPC settings.

### Class
`weaviate.config.AdditionalConfig`

### Parameters
- **connection** (ConnectionConfig) - Connection configuration object.
- **proxies** (str | Proxies | None) - Proxy settings, can be a URL string or a Proxies object.
- **timeout** (Tuple[int, int] | Timeout) - Timeout settings for queries and inserts, or a Timeout object for more granular control.
- **trust_env** (bool) - Whether to trust environment variables for proxy configuration.
- **grpc_config** (GrpcConfig | None) - gRPC configuration object.

### Request Example
```python
from weaviate.config import AdditionalConfig, ConnectionConfig, Proxies, Timeout

# Example with custom connection, proxies, and timeouts
connection = ConnectionConfig(host="localhost", port=8080)
proxies = Proxies(http="http://proxy.example.com:8080")
timeout = Timeout(init=10, query=60, insert=120)

additional_config = AdditionalConfig(
    connection=connection,
    proxies=proxies,
    timeout=timeout,
    trust_env=False,
    grpc_config=None  # Assuming no specific gRPC config for this example
)
```

### Response Example
```json
{
  "connection": {
    "host": "localhost",
    "port": 8080,
    "includes": [],
    "excludes": []
  },
  "proxies": {
    "http": "http://proxy.example.com:8080",
    "https": null,
    "grpc": null
  },
  "timeout": {
    "init": 10,
    "query": 60,
    "insert": 120
  },
  "trust_env": false,
  "grpc_config": null
}
```
```

--------------------------------

### Initialize FetchObjectsByIDs Classes

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.queries.fetch_objects_by_ids.md

Demonstrates the constructor signature for the synchronous and asynchronous fetch classes. These classes are used to define the query parameters for retrieving specific objects from a Weaviate collection.

```python
from weaviate.collections.queries.fetch_objects_by_ids import _FetchObjectsByIDsGenerate, _FetchObjectsByIDsGenerateAsync

# Synchronous initialization
sync_fetcher = _FetchObjectsByIDsGenerate(
    connection=connection,
    name="MyCollection",
    consistency_level=None,
    tenant=None,
    properties=None,
    references=None,
    validate_arguments=True
)

# Asynchronous initialization
async_fetcher = _FetchObjectsByIDsGenerateAsync(
    connection=connection,
    name="MyCollection",
    consistency_level=None,
    tenant=None,
    properties=None,
    references=None,
    validate_arguments=True
)
```

--------------------------------

### Proxies Configuration

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Configure proxy settings for HTTP, HTTPS, and gRPC connections to Weaviate.

```APIDOC
## Proxies Configuration

### Description
Configure proxy settings for sending requests to Weaviate through a proxy. This class allows specifying separate proxies for HTTP, HTTPS, and gRPC.

### Class
`weaviate.config.Proxies`

### Parameters
- **http** (str | None) - The proxy URL for HTTP connections.
- **https** (str | None) - The proxy URL for HTTPS connections.
- **grpc** (str | None) - The proxy URL for gRPC connections.

### Request Example
```python
from weaviate.config import Proxies

proxies = Proxies(http="http://localhost:8080", https="https://localhost:8080", grpc="http://localhost:8080")
```

### Response Example
```json
{
  "http": "http://localhost:8080",
  "https": "https://localhost:8080",
  "grpc": "http://localhost:8080"
}
```
```

--------------------------------

### Create Collection from Dictionary

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.collections.md

Creates a Weaviate collection using a pre-defined configuration dictionary and returns a collection object.

```APIDOC
## POST /weaviate/collections/create_from_dict

### Description
Creates a collection in Weaviate using a pre-defined Weaviate collection configuration dictionary object. This is helpful for v3 -> v4 migrations and experimental features.

### Method
POST

### Endpoint
/weaviate/collections/create_from_dict

### Parameters
#### Request Body
- **config** (*dict*) - Required - The dictionary representation of the collection’s configuration.

### Request Example
```json
{
  "config": {
    "name": "MyCollection",
    "properties": [
      {
        "name": "content",
        "dataType": ["text"]
      }
    ]
  }
}
```

### Response
#### Success Response (200)
- **Collection** (*Collection*) - The created collection object.

#### Response Example
```json
{
  "collection": {
    "name": "MyCollection"
  }
}
```

### Errors
- **WeaviateConnectionError**: If the network connection to Weaviate fails.
- **UnexpectedStatusCodeError**: If Weaviate reports a non-OK status.
```

--------------------------------

### Weaviate Client Initialization

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Initializes a WeaviateClient class instance for interacting with a Weaviate instance. Helper functions are available for cloud and local connections.

```APIDOC
## Weaviate Client Initialization

### Description
Initializes a WeaviateClient class instance to use when interacting with Weaviate. Use this specific initializer when you want to create a custom Client specific to your Weaviate setup. To simplify connections to Weaviate Cloud or local instances, use the `weaviate.connect_to_weaviate_cloud()` or `weaviate.connect_to_local()` helper functions.

### Parameters
#### Path Parameters
None

#### Query Parameters
None

#### Request Body
None

### Request Example
```python
import weaviate

client = weaviate.Client(
    connection_params=None,
    embedded_options=None,
    auth_client_secret=None,
    additional_headers=None,
    additional_config=None,
    skip_init_checks=False
)
```

### Response
#### Success Response (200)
None

#### Response Example
None
```

--------------------------------

### Tenant Management Classes

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.tenants.md

Details the synchronous and asynchronous client classes for managing tenants.

```APIDOC
## Tenant Management Classes

### Description
This section describes the `_Tenants` and `_TenantsAsync` classes used for managing tenants in Weaviate. These classes are part of the synchronous and asynchronous client implementations, respectively.

### Class: `_Tenants` (Synchronous)

#### Parameters
* **connection** (*ConnectionType*) - The connection object for interacting with Weaviate.
* **name** (*str*) - The name of the tenant.
* **validate_arguments** (*bool*) - Whether to validate arguments (default: True).

### Class: `_TenantsAsync` (Asynchronous)

#### Parameters
* **connection** (*ConnectionType*) - The connection object for interacting with Weaviate.
* **name** (*str*) - The name of the tenant.
* **validate_arguments** (*bool*) - Whether to validate arguments (default: True).

### Type Alias: `TenantOutputType`

`TenantOutputType` is an alias for `Tenant` from `weaviate.collections.classes.tenants.Tenant`.
```

--------------------------------

### Client Utility Methods

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Provides essential methods for managing the Weaviate client connection and retrieving configuration details.

```APIDOC
## Client Utility Methods

### Description
Provides essential methods for managing the Weaviate client connection and retrieving configuration details.

### Method: close()

#### Description
In order to clean up any resources used by the client, call this method when you are done with it. If you do not do this, memory leaks may occur due to stale connections. This method also closes the embedded database if one was started.

#### Endpoint
N/A (Method of the client object)

#### Return type
None | *Awaitable*[None]

### Method: connect()

#### Description
Connect to the Weaviate instance performing all the necessary checks. If you have specified skip_init_checks in the constructor then this method will not perform any runtime checks to ensure that Weaviate is running and ready to accept requests. This is useful for air-gapped environments and high-performance setups. This method is idempotent and will only perform the checks once. Any subsequent calls do nothing while client.is_connected() == True.

#### Raises
* [**WeaviateConnectionError**](weaviate.exceptions.md#weaviate.exceptions.WeaviateConnectionError) – If the network connection to weaviate fails.
* [**UnexpectedStatusCodeError**](weaviate.exceptions.md#weaviate.exceptions.UnexpectedStatusCodeError) – If weaviate reports a none OK status.

#### Return type
None | *Awaitable*[None]

### Method: get_meta()

#### Description
Get the meta endpoint description of weaviate.

#### Returns
The dict describing the weaviate configuration.

#### Raises
[**UnexpectedStatusCodeError**](weaviate.exceptions.md#weaviate.exceptions.UnexpectedStatusCodeError) – If Weaviate reports a none OK status.

#### Return type
dict | *Awaitable*[dict]

### Method: get_open_id_configuration()

#### Description
Get the openid-configuration.

#### Returns
The configuration or None if not configured.

#### Raises
[**UnexpectedStatusCodeError**](weaviate.exceptions.md#weaviate.exceptions.UnexpectedStatusCodeError) – If Weaviate reports a none OK status.

#### Return type
*Dict*[str, *Any*] | None | *Awaitable*[*Dict*[str, *Any*] | None]
```

--------------------------------

### RQConfigUpdate

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.classes.md

Configuration for Product Quantization (PQ) updates.

```python
class weaviate.collections.classes.config_vector_index._RQConfigUpdate(enabled: bool | None, rescoreLimit: int | None, bits: int | None)
```

--------------------------------

### MetadataQuery.full_with_profile class method

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.classes.md

Returns a MetadataQuery with all fields set to True, including query profiling.

```python
full_with_profile()
```

--------------------------------

### Connect to Weaviate with Custom Parameters (Python)

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Establishes a connection to a Weaviate instance using custom HTTP and gRPC host and port configurations. Supports secure connections and authentication. The client can be used directly or as a context manager for automatic connection closing.

```python
import weaviate

# Without Context Manager
client = weaviate.connect_to_custom(
    http_host="localhost",
    http_port=8080,
    http_secure=False,
    grpc_host="localhost",
    grpc_port=50051,
    grpc_secure=False,
)
print(client.is_ready())
client.close() # Close the connection when you are done with it.

# With Context Manager
with weaviate.connect_to_custom(
    http_host="localhost",
    http_port=8080,
    http_secure=False,
    grpc_host="localhost",
    grpc_port=50051,
    grpc_secure=False,
) as client:
    print(client.is_ready())
# The connection is automatically closed when the context is exited.
```

--------------------------------

### Check Weaviate Connection Status (Python)

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.md

Provides methods to check the status of the Weaviate client's connection. `is_connected()` verifies if the client has an open connection pool, while `is_live()` pings both HTTP and gRPC endpoints to ensure the Weaviate instance is responsive. `is_ready()` checks if the instance is ready to serve requests.

```python
# Check if connected
is_connected = client.is_connected()

# Check if live (HTTP and gRPC)
is_live = client.is_live()

# Check if ready
is_ready = client.is_ready()
```

--------------------------------

### Synchronous Tenant Management in Weaviate Python Client

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.tenants.md

Initializes the synchronous tenant manager for Weaviate. It requires a connection object, a name, and an optional argument for validating inputs. This class is designed for direct, blocking operations.

```python
from weaviate.collections.tenants import _Tenants

# Assuming 'connection' is an established ConnectionSync object
sync_tenants_manager = _Tenants(connection=connection, name="my_tenant_manager")
```

--------------------------------

### Create a Weaviate Collection from Dictionary

Source: https://github.com/weaviate/weaviate-python-client/blob/main/docs/weaviate.collections.collections.md

The 'create_from_dict' method allows for the creation of a collection in Weaviate using a raw configuration dictionary. This is particularly useful for v3 to v4 migrations or when utilizing experimental features not yet supported by the standard client interface.

```python
config = {
    "class": "MyCollection",
    "vectorizer": "text2vec-openai"
}
collection = client.collections.create_from_dict(config)
```
