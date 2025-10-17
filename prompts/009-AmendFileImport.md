Address design bug

Given
- I am using /api/sources/file
- I am importing text via file
- I have provided the following elements

{
  "notebook_id": "uuid"
  "name": "string",
  "file_path": "string",
  "file_type": "string",
}

When I invoke the api
Then 
- The system should fetch the content of the   file using infra level code
- The system should populate the content  based on the file content- 

The content parameter should not be expected 
  "file_type": "string",
  "file_size": 0,


