## setup
- Review spec - specs/clean_architecture.md
- Review openapi spec - openapi.json
- Following clean architecture style, implement folders for core, infrastructure
- Implement HttpClientService class for all openapi http calls
- Responses should be strongly typed following the openapi spec

## adjust angular front-end to work with python backend
- adjust the angular http clients so that they can work with our python api server
- in dev environment, the api server runs on https://musical-zebra-pj6xv5g7vwh7wxw-8000.app.github.dev/
- the api server should be configurable
- setup should help us avoid cors issue

## Handle making new notebook

Use discoveryPortal/src/app/infrastructure/http/notebook-api.service.ts

Use Create notebooks api 

Given
- I am using the new notebook component
- After I fill out all the valid properties of a notebook

When
- I click the "Save" button

Then
- The system properly  stores the notebook
- The system navigates me back to  'list-notebooks'

Properly report validation errors to the user if I do not fill out required fields.


## Implement edit-notebook component
- Review edit-notebook component code
- Screen features
    - system shows notebook name
    - system shows notebook description
    - system lists content sources linked to notebook

## Add delete note book
- On edit-notebook add button on right to enable user to delete a notebook
- Please make sure to confirm operation before execution
- After delete, navigate the user back to the list-notebooks screen.

## Add source / text
- Enable user to "add source from text" from "edit-notebook"
- Create component to enable me to add source to notebook using text
- Return the user to "edit-notebook" after adding source
- follow ui guidance

## Add source from url
- Enable user to "add source from url" from "edit-notebook"
- Create component to enable me to add source to notebook using url
- Return the user to "edit-notebook" after adding source
- follow ui guidance


## Add source from pdf
- Enable user to "add source from PDF" from "edit-notebook"
- UX needs to faciliate uploading PDF to api
- Create component to enable me to add source to notebook using PDF
- Process of adding pdf to server  takes 5 seconds.   Add  spinner ui for process
- Return the user to "edit-notebook" after adding source
- follow ui guidance

## Make blog post based on notebook and sources

User should be able to generate blog post
- Navigate to notebook(edit-notebook component)
- User clicks "new blog post" button
- Navigate to "new blog post" component
- On the "new blog post" component enables the user to fill out the following:
- blog title
- custom prompt
- tone(informative, causal,formal,conversational,academic)
- word count(550,700,1000)
- structure(default,how to, list article, comparison, case study,opinion)
- blog post should be generated using retrieval augmented generation using segments most closely linked to the prompt
- the API will take 5 seconds to run. make sure ux includes spinner during the blog post generation process
- store the blog post as an output record using api
- display the content of blog post

## output list screen

as a user, I should be able to navigate to a component so that I can see the list of output records connected to my notebook
- I should be able to see the list of output records
- I should be able to see the type of output record
- I should be able to open the output records and view it's contents