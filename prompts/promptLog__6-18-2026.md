- review src backend.
- need to remove all firebase auth code
- think about changes and document in removeFirebaseAuth.md
===
- review removeFirebaseAuth.md
- think about adding a registration and auth system internal to the backend
- the system should use oauth patterns and jwt tokens
- document proposal in oauth_local.md
===
Review to get context of app goals: specs/domain_model.md

Think about making a new front-end using React.
Implement react project in discoveryPortalReact

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
