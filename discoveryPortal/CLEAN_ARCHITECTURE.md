# Discovery Portal - Clean Architecture Implementation

This document describes the clean architecture implementation for the Discovery Portal Angular application.

## Architecture Overview

The application follows Clean Architecture principles as advocated by Steve Smith (Ardalis), with clear separation between:

- **Core**: Business logic and domain models (framework-independent)
- **Infrastructure**: External concerns like HTTP communication
- **UI/Presentation**: Angular components and views

## Folder Structure

```
src/app/
├── core/                          # Core business logic layer
│   ├── models/                    # Domain models and DTOs
│   │   ├── notebook.models.ts     # Notebook domain models
│   │   ├── source.models.ts       # Source domain models
│   │   ├── output.models.ts       # Output domain models
│   │   ├── vector.models.ts       # Vector search domain models
│   │   ├── common.models.ts       # Shared models
│   │   └── index.ts              # Barrel export
│   ├── interfaces/                # Core interfaces
│   └── services/                  # Domain services
│
├── infrastructure/                # Infrastructure layer
│   ├── http/                      # HTTP client services
│   │   ├── http-client.service.ts           # Base HTTP client
│   │   ├── notebook-api.service.ts          # Notebook API
│   │   ├── source-api.service.ts            # Source API
│   │   ├── output-api.service.ts            # Output API
│   │   ├── vector-search-api.service.ts     # Vector search API
│   │   ├── article-search-api.service.ts    # Article search API
│   │   └── index.ts                         # Barrel export
│   └── config/                    # Configuration services
│       ├── api-config.service.ts  # API configuration
│       └── index.ts              # Barrel export
│
└── [components/features]          # Presentation layer
```

## Core Layer

### Models (`core/models/`)

All models are **strongly typed** according to the OpenAPI specification:

- **notebook.models.ts**: Notebook entities, requests, and responses
- **source.models.ts**: Source entities (file, URL, text)
- **output.models.ts**: Output/generation entities
- **vector.models.ts**: Vector search and RAG models
- **common.models.ts**: Shared models (errors, results, etc.)

#### Key Principles:
- ✅ Minimal external dependencies
- ✅ Framework-independent TypeScript interfaces
- ✅ Strongly typed based on OpenAPI schemas
- ✅ Exported through barrel files for clean imports

## Infrastructure Layer

### HTTP Client Service (`infrastructure/http/`)

#### Base HTTP Client (`http-client.service.ts`)

Provides foundational HTTP operations with:
- Centralized error handling
- Automatic URL construction
- Type-safe request/response handling
- Observable-based API
- AppResult pattern support

```typescript
// Example usage
get<T>(endpoint: string, options?: HttpOptions): Observable<T>
post<T>(endpoint: string, body: unknown, options?: HttpOptions): Observable<T>
put<T>(endpoint: string, body: unknown, options?: HttpOptions): Observable<T>
patch<T>(endpoint: string, body: unknown, options?: HttpOptions): Observable<T>
delete<T>(endpoint: string, options?: HttpOptions): Observable<T>
```

#### API Services

All API services follow the same pattern:

**NotebookApiService** - Notebook operations
```typescript
- createNotebook(request: CreateNotebookRequest): Observable<NotebookResponse>
- getNotebook(notebookId: string): Observable<NotebookResponse>
- listNotebooks(params?: ListNotebooksParams): Observable<NotebookListResponse>
- updateNotebook(notebookId: string, request: UpdateNotebookRequest): Observable<NotebookResponse>
- deleteNotebook(notebookId: string, cascade?: boolean): Observable<void>
- renameNotebook(notebookId: string, request: RenameNotebookRequest): Observable<NotebookResponse>
- addTags(notebookId: string, request: AddTagsRequest): Observable<NotebookResponse>
- removeTags(notebookId: string, request: RemoveTagsRequest): Observable<NotebookResponse>
- generateBlogPost(notebookId: string, request: GenerateBlogPostRequest): Observable<OutputResponse>
```

**SourceApiService** - Source operations
```typescript
- importFileSource(request: ImportFileSourceRequest): Observable<SourceResponse>
- importUrlSource(request: ImportUrlSourceRequest): Observable<SourceResponse>
- importTextSource(request: ImportTextSourceRequest): Observable<SourceResponse>
- getSource(sourceId: string, includeDeleted?: boolean): Observable<SourceResponse>
- listSourcesByNotebook(params: ListSourcesParams): Observable<SourceListResponse>
- deleteSource(sourceId: string, notebookId: string): Observable<void>
- renameSource(sourceId: string, request: RenameSourceRequest): Observable<SourceResponse>
- restoreSource(sourceId: string, notebookId: string): Observable<SourceResponse>
- extractContent(sourceId: string, request: ExtractContentRequest): Observable<SourceResponse>
- getSourcePreview(sourceId: string, length?: number): Observable<SourcePreviewResponse>
- addSourcesBySearch(request: AddSourcesBySearchRequest): Observable<AddSourcesBySearchResponse>
```

**OutputApiService** - Output operations
```typescript
- createOutput(notebookId: string, request: CreateOutputRequest): Observable<OutputResponse>
- getOutput(outputId: string): Observable<OutputResponse>
- listOutputs(params?: ListOutputsParams): Observable<OutputListResponse>
- updateOutput(outputId: string, request: UpdateOutputRequest): Observable<OutputResponse>
- deleteOutput(outputId: string): Observable<void>
- searchOutputs(params: SearchOutputsParams): Observable<OutputListResponse>
- getOutputPreview(outputId: string, length?: number): Observable<OutputPreviewResponse>
```

**VectorSearchApiService** - Vector search and RAG operations
```typescript
- ingestNotebook(notebookId: string, request?: IngestNotebookRequest): Observable<IngestNotebookResponse>
- searchSimilarContent(notebookId: string, query: string, limit?: number): Observable<SimilaritySearchResponse>
- getVectorCount(notebookId: string): Observable<VectorCountResponse>
- deleteNotebookVectors(notebookId: string): Observable<void>
- createCollection(notebookId: string, request?: CreateCollectionRequest): Observable<CreateCollectionResponse>
- askQuestion(notebookId: string, request: AskQuestionRequest): Observable<QaResponse>
- getQaHealth(): Observable<QaHealthResponse>
- generateMindMap(notebookId: string, request: GenerateMindMapRequest): Observable<MindMapResponse>
- getMindMapViewer(notebookId: string): Observable<string>
```

**ArticleSearchApiService** - Article search operations
```typescript
- searchArticles(request: ArticleSearchRequest): Observable<ArticleSearchResponse>
```

### Configuration (`infrastructure/config/`)

#### API Configuration Service (`api-config.service.ts`)

Manages API endpoints and configuration:
- Base URL management
- Environment-aware defaults
- Timeout configuration

```typescript
getBaseUrl(): string
setBaseUrl(url: string): void
getTimeout(): number
setTimeout(timeout: number): void
```

## Usage Examples

### Basic Usage

```typescript
import { Component, inject } from '@angular/core';
import { NotebookApiService } from './infrastructure/http';
import { CreateNotebookRequest, NotebookResponse } from './core/models';

@Component({
  selector: 'app-notebook-create',
  template: '...'
})
export class NotebookCreateComponent {
  private notebookApi = inject(NotebookApiService);

  createNotebook(): void {
    const request: CreateNotebookRequest = {
      name: 'My Research Notebook',
      description: 'A notebook for AI research',
      tags: ['AI', 'Research']
    };

    this.notebookApi.createNotebook(request).subscribe({
      next: (notebook: NotebookResponse) => {
        console.log('Created notebook:', notebook);
      },
      error: (error) => {
        console.error('Failed to create notebook:', error);
      }
    });
  }
}
```

### Listing with Filters

```typescript
import { Component, inject, OnInit } from '@angular/core';
import { NotebookApiService } from './infrastructure/http';
import { NotebookListResponse } from './core/models';

@Component({
  selector: 'app-notebook-list',
  template: '...'
})
export class NotebookListComponent implements OnInit {
  private notebookApi = inject(NotebookApiService);
  notebooks: NotebookResponse[] = [];

  ngOnInit(): void {
    this.notebookApi.listNotebooks({
      tags: ['AI'],
      sort_by: 'updated_at',
      sort_order: 'desc',
      limit: 10
    }).subscribe({
      next: (response: NotebookListResponse) => {
        this.notebooks = response.notebooks;
      }
    });
  }
}
```

### Error Handling

```typescript
import { Component, inject } from '@angular/core';
import { SourceApiService } from './infrastructure/http';

@Component({
  selector: 'app-source-import',
  template: '...'
})
export class SourceImportComponent {
  private sourceApi = inject(SourceApiService);

  importUrl(notebookId: string, url: string): void {
    this.sourceApi.importUrlSource({
      notebook_id: notebookId,
      url: url
    }).subscribe({
      next: (source) => {
        console.log('Imported source:', source);
      },
      error: (error) => {
        // Error object contains:
        // - message: string
        // - status: number
        // - statusText: string
        // - validationErrors?: ValidationErrorResponse
        
        if (error.validationErrors) {
          console.error('Validation errors:', error.validationErrors);
        } else {
          console.error('Error:', error.message);
        }
      }
    });
  }
}
```

### RAG Operations

```typescript
import { Component, inject } from '@angular/core';
import { VectorSearchApiService } from './infrastructure/http';
import { AskQuestionRequest, QaResponse } from './core/models';

@Component({
  selector: 'app-qa-interface',
  template: '...'
})
export class QaInterfaceComponent {
  private vectorApi = inject(VectorSearchApiService);

  askQuestion(notebookId: string, question: string): void {
    const request: AskQuestionRequest = {
      question: question,
      max_sources: 5,
      temperature: 0.3
    };

    this.vectorApi.askQuestion(notebookId, request).subscribe({
      next: (response: QaResponse) => {
        console.log('Answer:', response.answer);
        console.log('Sources:', response.sources);
        console.log('Confidence:', response.confidence_score);
      }
    });
  }
}
```

## Clean Architecture Compliance

### ✅ Dependency Rule
- Core has **zero dependencies** on Infrastructure
- Infrastructure depends on Core models
- All dependencies point inward

### ✅ Interface Definition
- Core defines all interfaces and models
- Infrastructure implements HTTP operations against these contracts

### ✅ Testability
- Core models are pure TypeScript interfaces (easily testable)
- Infrastructure services can be mocked using interfaces
- No framework coupling in business logic

### ✅ Strong Typing
- All requests and responses are strongly typed
- TypeScript interfaces generated from OpenAPI spec
- Compile-time type safety throughout

## Configuration

### Development
The API configuration automatically detects localhost and uses port 8000:

```typescript
// Default: http://localhost:8000
```

### Production
Set the base URL explicitly:

```typescript
import { ApiConfigService } from './infrastructure/config';

const config = inject(ApiConfigService);
config.setBaseUrl('https://api.yourdomain.com');
```

## Best Practices

1. **Always use strongly typed requests/responses**
   - Import from `core/models`
   - Let TypeScript catch errors at compile time

2. **Handle errors appropriately**
   - Subscribe with error callbacks
   - Check for validation errors
   - Display user-friendly messages

3. **Use dependency injection**
   - Inject services via Angular's DI
   - Makes testing easier
   - Follows Angular conventions

4. **Keep business logic in Core**
   - Don't put business rules in API services
   - API services are for HTTP operations only
   - Use domain services for complex logic

5. **Leverage RxJS operators**
   - Transform data with `map`, `filter`, etc.
   - Combine streams with `combineLatest`, `merge`
   - Handle errors with `catchError`

## Future Enhancements

- [ ] Add retry logic for failed requests
- [ ] Implement request caching
- [ ] Add request interceptors for auth
- [ ] Create domain service layer
- [ ] Add state management integration
- [ ] Implement offline support
- [ ] Add request/response logging
- [ ] Create mock API services for testing

## Contributing

When adding new API endpoints:

1. Update OpenAPI specification
2. Add models to appropriate `core/models/*.models.ts`
3. Add methods to relevant API service in `infrastructure/http/`
4. Update this documentation
5. Add unit tests for new functionality
