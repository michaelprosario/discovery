

Error during this call...

curl -X 'POST' \
  'https://musical-zebra-pj6xv5g7vwh7wxw-8000.app.github.dev/api/sources/file' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "notebook_id": "6cfae25b-0fb9-4052-a89a-f316dc77d852",
  "name": "test",
  "file_path": "/workspaces/discovery/QUICK_START.md",
  "file_type": "md"
}'


INFO:     67.8.144.81:0 - "GET / HTTP/1.1" 200 OK
INFO:     67.8.144.81:0 - "GET /docs HTTP/1.1" 200 OK
INFO:     67.8.144.81:0 - "GET /openapi.json HTTP/1.1" 200 OK
INFO:     67.8.144.81:0 - "POST /api/sources/file HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/uvicorn/protocols/http/httptools_impl.py", line 419, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/uvicorn/middleware/proxy_headers.py", line 84, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/fastapi/applications.py", line 1054, in __call__
    await super().__call__(scope, receive, send)
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/applications.py", line 123, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 91, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 146, in simple_response
    await self.app(scope, receive, send)
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 62, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 64, in wrapped_app
    raise exc
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    await app(scope, receive, sender)
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/routing.py", line 762, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/routing.py", line 782, in app
    await route.handle(scope, receive, send)
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/routing.py", line 297, in handle
    await self.app(scope, receive, send)
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/routing.py", line 77, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 64, in wrapped_app
    raise exc
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    await app(scope, receive, sender)
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/routing.py", line 72, in app
    response = await func(request)
               ^^^^^^^^^^^^^^^^^^^
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 299, in app
    raise e
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 294, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 193, in run_endpoint_function
    return await run_in_threadpool(dependant.call, **values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/starlette/concurrency.py", line 40, in run_in_threadpool
    return await anyio.to_thread.run_sync(func, *args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/anyio/to_thread.py", line 56, in run_sync
    return await get_async_backend().run_sync_in_worker_thread(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/anyio/_backends/_asyncio.py", line 2485, in run_sync_in_worker_thread
    return await future
           ^^^^^^^^^^^^
  File "/workspaces/discovery/.venv/lib/python3.12/site-packages/anyio/_backends/_asyncio.py", line 976, in run
    result = context.run(func, *args)
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/discovery/src/api/sources_router.py", line 214, in import_file_source
    result = service.import_file_source(command)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/discovery/src/core/services/source_ingestion_service.py", line 135, in import_file_source
    store_result = self._file_storage_provider.store_file(command.file_content, storage_path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'store_file'