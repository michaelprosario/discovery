# DiscoveryPortal

This project was generated using [Angular CLI](https://github.com/angular/angular-cli) version 21.0.0.

## Features

### Chat with Notebook (Q&A Interface)
The Discovery Portal includes an intelligent chat interface that allows you to have conversations with your notebook content using RAG (Retrieval-Augmented Generation).

**Key Features:**
- **Conversational Interface**: Ask questions in natural language about your notebook sources
- **Context-Aware Responses**: The AI assistant provides answers based only on the content in your notebook's sources
- **Source Citations**: Every answer includes references to the relevant source chunks with:
  - Source name and type
  - Relevance score
  - Clickable links to original sources (for URL sources)
  - Text excerpts showing where the information came from
- **Real-time Processing**: See typing indicators while the AI processes your question
- **Chat History**: Maintain conversation context throughout your session
- **Clear Chat**: Reset the conversation at any time

**How to Use:**
1. Navigate to a notebook from the notebook list
2. Click the "Chat with Notebook" button (teal colored)
3. Type your question in the input field at the bottom
4. Press Enter to send (or Shift+Enter for new lines)
5. Review the AI's response and explore the related source citations
6. Click on source references to open the original URLs in a new tab

**Technical Details:**
- Uses vector similarity search to find relevant content chunks
- Powered by LLM (Gemini) for natural language understanding
- Configurable parameters: max_sources, temperature, max_tokens
- Responsive design supporting both light and dark modes

## Development server

To start a local development server, run:

```bash
ng serve
```

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

## Running unit tests

To execute unit tests with the [Karma](https://karma-runner.github.io) test runner, use the following command:

```bash
ng test
```

## Running end-to-end tests

For end-to-end (e2e) testing, run:

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.
