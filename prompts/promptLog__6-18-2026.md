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

## mindmapt output

- Please read the docs related to https://markmap.js.org/docs/packages--markmap-autoloader
- As a discovery user, I should like the ability to build a mind map based on prompt input to help me learn aspects of my notebook.
- The prompt input should use the vector search database and the llm provider to make an outline answering the prompt using markdown
- I should be able to view the mindmap
- The mindmap data should be stored as an aoutput record connected to the notebook
- The system should enable me to download the outline markdown

make sure to read markmap.html as an example
I tested the mindmap generation feature
The system produced markup grounded on the sources of the notebook. This is great
The system did not visualize the markdown output using the markmap library
Please correct this.


### Refactor - Create separated components for viewing blog posts vs. mindmap outputs

- Review the /workspaces/discovery/discoveryPortal/src/app/view-output/view-output.html
- Review /workspaces/discovery/discoveryPortal/src/app/view-output/view-output.ts
- In a future state of the system, we will have more output types besides blog posts and mindmaps
- Let's create different components for viewing each output type


## chat Question answer interface

As a user, I should be able to chat with an agent
- the agent should be a helpful agent that replies only upon the context obtained from the vector database
- implement question and answer agent on a notebook based on data ingested
- implement RAG agent using content similarity services
- the agent should promote a conversational way to explore the sources in the notebook
- The system should show related sources to help me gain trust in the answers of the agent. 
- I should be able to open source reference links with a click

### 6/18

- review src backend.
- need to remove all firebase auth code
- think about changes and document in removeFirebaseAuth.md
===
- review removeFirebaseAuth.md
- think about adding a registration and auth system internal to the backend
- the system should use oauth patterns and jwt tokens
- document proposal in oauth_local.md
===
-Review to get context of app goals: specs/domain_model.md
-Think about making a new front-end using React.
-Implement react project in discoveryPortalReact
-Make sure that discoveryPortalReact properly proxies to local backend for local dev
-We will probably host a static build of the react front end on the FAST API (in the future)

The system should focus upon the following use cases
- User registration
- User login
- CreateNotebookCommand
- UpdateNotebookCommand
- RenameNotebookCommand
- ImportFileSource
- ImportUrlSource
- DeleteSource
- ExtractContent
- GenerateSummary
- IndexContentCommand
- ArticleSearchQuery
- GetNotebookByIdQuery
- ListNotebooksQuery
- ListSources
- GetSource
- Generation of blog posts
- Question and answer with notebook
    - make sure to cite sources
===

Given
- I am using the view blog output page

When 
- I click the "read" button

Then
- The system should do text to speech to enable me to listen to the article.
- The system should give me the following functions too
    - pause reading
    - resume reading
    - restart reading

===

Given 
- I am using article search

When 
- I click "create notebook"

Then
- The system should note all the articles in the search results
- The system should enable me to create a notebook and select which articles should be added as sources to the notebook.

===

Given
- I am creating a notebook from sources from article search
- I have selected 1 or many sources for notebook creation

When
- I click "Create notebook"

Then
- The system should do the following
    - Create notebook record
    - Create notebook source records for each source
    - When the process finishes, the system should report the following:
        - articles added with no issues
        - list articles that could not be ingested

Think about these requirements and document in buildNotebookFromSearch.md

===

Write a script
- explore discoveryPortalReact
- do a build so that we have html/js that we can deploy
- move the dist directory content to src/api/static
===
- Update discoveryPortalReact
- Make screens responsive and more mobile friendly.
===
- explore discoveryPortalReact

Given
- I am reviewing an existing notebook
- I have populated a search term in the search field
- I have clicked "Search"
- The system has rendered a list of articles
- I have selected 1 or many sources for notebook creation

When
- I click "Add sources to notebook"

Then
- The system should do the following
    - Create notebook source records for each source
    - When the process finishes, the system should report the following:
        - articles added with no issues
        - list articles that could not be ingested

Think about these requirements and document in addSourcesToNotebook.md
