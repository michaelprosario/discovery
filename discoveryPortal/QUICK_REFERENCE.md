# Clean Architecture Quick Reference

## Import Paths

```typescript
// Core Models
import { 
  NotebookResponse, 
  CreateNotebookRequest,
  SourceResponse,
  OutputResponse
} from './core/models';

// Infrastructure Services
import {
  NotebookApiService,
  SourceApiService,
  OutputApiService,
  VectorSearchApiService,
  ApiConfigService
} from './infrastructure';
```

## Common Patterns

### 1. Create a Notebook

```typescript
const request: CreateNotebookRequest = {
  name: 'My Notebook',
  description: 'Optional description',
  tags: ['tag1', 'tag2']
};

notebookApi.createNotebook(request).subscribe({
  next: (notebook: NotebookResponse) => {
    console.log('Created:', notebook.id);
  },
  error: (error) => {
    console.error('Error:', error.message);
  }
});
```

### 2. List Notebooks with Filtering

```typescript
notebookApi.listNotebooks({
  tags: ['AI', 'Research'],
  sort_by: 'updated_at',
  sort_order: 'desc',
  limit: 20,
  offset: 0
}).subscribe(response => {
  console.log('Found:', response.total);
  console.log('Notebooks:', response.notebooks);
});
```

### 3. Import a URL Source

```typescript
sourceApi.importUrlSource({
  notebook_id: notebookId,
  url: 'https://example.com/article',
  title: 'Optional title'
}).subscribe(source => {
  console.log('Imported:', source.name);
});
```

### 4. Import a Text Source

```typescript
sourceApi.importTextSource({
  notebook_id: notebookId,
  title: 'My Notes',
  content: 'Some text content...'
}).subscribe(source => {
  console.log('Created:', source.id);
});
```

### 5. Import a File Source (Base64)

```typescript
// Convert file to base64 first
const base64Content = await fileToBase64(file);

sourceApi.importFileSource({
  notebook_id: notebookId,
  name: file.name,
  file_content: base64Content,
  file_type: 'pdf' // or 'docx', 'doc', 'txt', 'md'
}).subscribe(source => {
  console.log('Uploaded:', source.name);
});
```

### 6. Generate a Blog Post

```typescript
notebookApi.generateBlogPost(notebookId, {
  title: 'AI in Healthcare',
  target_word_count: 550,
  tone: 'informative',
  include_references: true
}).subscribe(output => {
  console.log('Generated:', output.content);
});
```

### 7. Ingest Notebook for Vector Search

```typescript
vectorApi.ingestNotebook(notebookId, {
  chunk_size: 1000,
  overlap: 200,
  force_reingest: false
}).subscribe(result => {
  console.log('Ingested:', result.chunks_ingested, 'chunks');
});
```

### 8. Ask a Question (RAG)

```typescript
vectorApi.askQuestion(notebookId, {
  question: 'What is machine learning?',
  max_sources: 5,
  temperature: 0.3,
  max_tokens: 1500
}).subscribe(response => {
  console.log('Answer:', response.answer);
  console.log('Sources:', response.sources.length);
  console.log('Confidence:', response.confidence_score);
});
```

### 9. Search Similar Content

```typescript
vectorApi.searchSimilarContent(
  notebookId,
  'neural networks',
  10 // limit
).subscribe(response => {
  console.log('Found:', response.results.length, 'similar chunks');
  response.results.forEach(result => {
    console.log('Certainty:', result.certainty);
    console.log('Text:', result.text.substring(0, 100));
  });
});
```

### 10. Generate Mind Map

```typescript
vectorApi.generateMindMap(notebookId, {
  prompt: 'Create a mind map of AI concepts',
  max_sources: 10,
  temperature: 0.4
}).subscribe(response => {
  console.log('Markdown outline:', response.markdown_outline);
  // Use markmap.js to visualize
});
```

## Error Handling

### Standard Error

```typescript
service.someMethod().subscribe({
  error: (error) => {
    console.error('Status:', error.status);
    console.error('Message:', error.message);
  }
});
```

### Validation Errors

```typescript
service.createSomething(data).subscribe({
  error: (error) => {
    if (error.validationErrors) {
      error.validationErrors.validation_errors.forEach(ve => {
        console.log(`${ve.field}: ${ve.message}`);
      });
    }
  }
});
```

## Configuration

### Set API Base URL

```typescript
import { ApiConfigService } from './infrastructure';

constructor(private config: ApiConfigService) {
  this.config.setBaseUrl('http://localhost:8000');
}
```

### Get Configuration

```typescript
const baseUrl = this.config.getBaseUrl();
const timeout = this.config.getTimeout();
```

## Type Safety

All responses are strongly typed:

```typescript
// ✅ Type-safe
notebookApi.getNotebook(id).subscribe((notebook: NotebookResponse) => {
  const name: string = notebook.name;
  const tags: string[] = notebook.tags;
  const createdAt: string = notebook.created_at;
});

// ❌ TypeScript will catch this
notebookApi.getNotebook(id).subscribe((notebook) => {
  const invalid = notebook.nonExistentField; // Error!
});
```

## RxJS Patterns

### Transform Response

```typescript
notebookApi.listNotebooks()
  .pipe(
    map(response => response.notebooks),
    map(notebooks => notebooks.filter(n => n.tags.includes('AI')))
  )
  .subscribe(aiNotebooks => {
    console.log('AI Notebooks:', aiNotebooks);
  });
```

### Combine Multiple Requests

```typescript
import { forkJoin } from 'rxjs';

forkJoin({
  notebook: notebookApi.getNotebook(notebookId),
  sources: sourceApi.listSourcesByNotebook({ notebook_id: notebookId }),
  outputs: outputApi.listOutputs({ notebook_id: notebookId })
}).subscribe(({ notebook, sources, outputs }) => {
  console.log('Notebook:', notebook.name);
  console.log('Sources:', sources.total);
  console.log('Outputs:', outputs.total);
});
```

### Sequential Requests

```typescript
import { switchMap } from 'rxjs/operators';

notebookApi.createNotebook({ name: 'New Notebook' })
  .pipe(
    switchMap(notebook => 
      sourceApi.importTextSource({
        notebook_id: notebook.id,
        title: 'First Source',
        content: 'Content...'
      })
    )
  )
  .subscribe(source => {
    console.log('Created notebook and added source:', source.id);
  });
```

## Service Injection

```typescript
import { Component, inject } from '@angular/core';
import { NotebookApiService } from './infrastructure';

@Component({
  selector: 'app-example',
  template: '...'
})
export class ExampleComponent {
  // Modern inject function
  private notebookApi = inject(NotebookApiService);
  
  // Or constructor injection
  constructor(
    private readonly notebookApi: NotebookApiService
  ) {}
}
```
