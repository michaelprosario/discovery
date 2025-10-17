Address design bug

Given
- I am using /api/sources/url`
- I am importing a text file via  a url
- I have provided valid inputs for notebook_id, name, url, title

When I invoke the api
Then 
- The system should fetch the content of the  url using infra level code
- The system should populate the content field based on the url fetch data

The content parameter should not be expected on  the  /api/sources/url

