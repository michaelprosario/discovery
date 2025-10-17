Address design bug

Given
- I am using /api/sources/file
- I am importing text via file
- I have provied valid inputs for notebook_id, name , file, title

When I invoke the api
Then 
- The system should fetch the content of the   file using infra level code
- The system should populate the cfile content  based on the file content- 

The content parameter should not be expected 
