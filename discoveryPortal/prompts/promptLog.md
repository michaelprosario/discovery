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
