/**
 * Example component demonstrating Clean Architecture API usage
 * This file serves as a reference implementation
 */

import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { 
  NotebookApiService, 
  SourceApiService, 
  OutputApiService,
  VectorSearchApiService 
} from '../infrastructure';
import { 
  NotebookResponse, 
  CreateNotebookRequest,
  SourceResponse,
  QaResponse,
  AppResult 
} from '../core/models';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { of } from 'rxjs';

interface NotebookWithDetails extends NotebookResponse {
  sources?: SourceResponse[];
  loading?: boolean;
}

@Component({
  selector: 'app-notebook-example',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="notebook-example">
      <h2>Notebook Manager Example</h2>
      
      <!-- Create Notebook Section -->
      <section class="create-section">
        <h3>Create Notebook</h3>
        <button (click)="createExampleNotebook()">Create Example Notebook</button>
        @if (createdNotebook()) {
          <div class="success">
            Created: {{ createdNotebook()!.name }} ({{ createdNotebook()!.id }})
          </div>
        }
      </section>

      <!-- List Notebooks Section -->
      <section class="list-section">
        <h3>Notebooks ({{ notebooks().length }})</h3>
        <button (click)="loadNotebooks()">Refresh List</button>
        
        @if (loading()) {
          <div class="loading">Loading...</div>
        }
        
        <div class="notebook-list">
          @for (notebook of notebooks(); track notebook.id) {
            <div class="notebook-card">
              <h4>{{ notebook.name }}</h4>
              <p>{{ notebook.description }}</p>
              <div class="meta">
                <span>Sources: {{ notebook.source_count }}</span>
                <span>Outputs: {{ notebook.output_count }}</span>
                <span>Tags: {{ notebook.tags.join(', ') }}</span>
              </div>
              <div class="actions">
                <button (click)="loadNotebookSources(notebook.id)">
                  Load Sources
                </button>
                <button (click)="askQuestion(notebook.id)">
                  Ask Question
                </button>
                <button (click)="deleteNotebook(notebook.id)">
                  Delete
                </button>
              </div>
              
              @if (notebook.sources) {
                <div class="sources">
                  <h5>Sources ({{ notebook.sources.length }})</h5>
                  @for (source of notebook.sources; track source.id) {
                    <div class="source-item">
                      <strong>{{ source.name }}</strong>
                      <span class="type">{{ source.source_type }}</span>
                    </div>
                  }
                </div>
              }
            </div>
          }
        </div>
      </section>

      <!-- QA Section -->
      @if (qaAnswer()) {
        <section class="qa-section">
          <h3>QA Answer</h3>
          <div class="answer">
            <p><strong>Question:</strong> {{ qaAnswer()!.question }}</p>
            <p><strong>Answer:</strong> {{ qaAnswer()!.answer }}</p>
            <p><strong>Confidence:</strong> {{ qaAnswer()!.confidence_score }}</p>
            <div class="sources">
              <h4>Sources Used:</h4>
              @for (source of qaAnswer()!.sources; track source.chunk_index) {
                <div class="source">
                  <p>{{ source.text.substring(0, 100) }}...</p>
                  <small>Relevance: {{ source.relevance_score }}</small>
                </div>
              }
            </div>
          </div>
        </section>
      }

      <!-- Error Display -->
      @if (error()) {
        <div class="error">
          Error: {{ error() }}
        </div>
      }
    </div>
  `,
  styles: [`
    .notebook-example {
      padding: 20px;
      max-width: 1200px;
      margin: 0 auto;
    }

    section {
      margin-bottom: 30px;
      padding: 20px;
      border: 1px solid #ddd;
      border-radius: 8px;
    }

    .notebook-card {
      padding: 15px;
      margin: 10px 0;
      border: 1px solid #eee;
      border-radius: 4px;
      background: #f9f9f9;
    }

    .meta {
      display: flex;
      gap: 15px;
      margin: 10px 0;
      font-size: 0.9em;
      color: #666;
    }

    .actions {
      display: flex;
      gap: 10px;
      margin-top: 10px;
    }

    button {
      padding: 8px 16px;
      background: #007bff;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }

    button:hover {
      background: #0056b3;
    }

    .success {
      padding: 10px;
      margin-top: 10px;
      background: #d4edda;
      color: #155724;
      border-radius: 4px;
    }

    .error {
      padding: 10px;
      margin-top: 10px;
      background: #f8d7da;
      color: #721c24;
      border-radius: 4px;
    }

    .loading {
      padding: 10px;
      color: #666;
      font-style: italic;
    }

    .sources {
      margin-top: 15px;
      padding: 10px;
      background: white;
      border-radius: 4px;
    }

    .source-item {
      display: flex;
      justify-content: space-between;
      padding: 5px;
      border-bottom: 1px solid #eee;
    }

    .type {
      color: #666;
      font-size: 0.9em;
    }

    .answer {
      background: white;
      padding: 15px;
      border-radius: 4px;
    }

    .source {
      padding: 10px;
      margin: 10px 0;
      background: #f9f9f9;
      border-left: 3px solid #007bff;
    }
  `]
})
export class NotebookExampleComponent implements OnInit {
  // Inject API services using the modern inject() function
  private notebookApi = inject(NotebookApiService);
  private sourceApi = inject(SourceApiService);
  private outputApi = inject(OutputApiService);
  private vectorApi = inject(VectorSearchApiService);

  // Component state using signals
  notebooks = signal<NotebookWithDetails[]>([]);
  createdNotebook = signal<NotebookResponse | null>(null);
  qaAnswer = signal<QaResponse | null>(null);
  loading = signal(false);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.loadNotebooks();
  }

  /**
   * Example: Create a new notebook
   */
  createExampleNotebook(): void {
    const request: CreateNotebookRequest = {
      name: `Research Notebook ${Date.now()}`,
      description: 'An example notebook created from the demo',
      tags: ['example', 'demo', 'clean-architecture']
    };

    this.loading.set(true);
    this.error.set(null);

    this.notebookApi.createNotebook(request).pipe(
      tap(notebook => {
        this.createdNotebook.set(notebook);
        console.log('Created notebook:', notebook);
      }),
      catchError(error => {
        this.error.set(error.message);
        return of(null);
      })
    ).subscribe(() => {
      this.loading.set(false);
      // Reload the list to show the new notebook
      this.loadNotebooks();
    });
  }

  /**
   * Example: Load all notebooks with filtering
   */
  loadNotebooks(): void {
    this.loading.set(true);
    this.error.set(null);

    this.notebookApi.listNotebooks({
      sort_by: 'updated_at',
      sort_order: 'desc',
      limit: 10
    }).pipe(
      tap(response => {
        console.log('Loaded notebooks:', response.total);
      }),
      map(response => response.notebooks),
      catchError(error => {
        this.error.set(error.message);
        return of([]);
      })
    ).subscribe(notebooks => {
      this.notebooks.set(notebooks);
      this.loading.set(false);
    });
  }

  /**
   * Example: Load sources for a notebook
   */
  loadNotebookSources(notebookId: string): void {
    this.sourceApi.listSourcesByNotebook({
      notebook_id: notebookId,
      sort_by: 'created_at',
      sort_order: 'desc'
    }).pipe(
      tap(response => {
        console.log('Loaded sources:', response.total);
      }),
      catchError(error => {
        this.error.set(error.message);
        return of({ sources: [], total: 0 });
      })
    ).subscribe(response => {
      // Update the notebook in the list with its sources
      this.notebooks.update(notebooks => 
        notebooks.map(n => 
          n.id === notebookId 
            ? { ...n, sources: response.sources }
            : n
        )
      );
    });
  }

  /**
   * Example: Ask a question using RAG
   */
  askQuestion(notebookId: string): void {
    // First, ensure the notebook is ingested
    this.vectorApi.ingestNotebook(notebookId, {
      chunk_size: 1000,
      overlap: 200,
      force_reingest: false
    }).pipe(
      tap(result => {
        console.log('Ingested chunks:', result.chunks_ingested);
      }),
      // Then ask the question
      switchMap(() => 
        this.vectorApi.askQuestion(notebookId, {
          question: 'What are the main topics covered in this notebook?',
          max_sources: 5,
          temperature: 0.3
        })
      ),
      catchError(error => {
        this.error.set(error.message);
        return of(null);
      })
    ).subscribe(answer => {
      if (answer) {
        this.qaAnswer.set(answer);
        console.log('QA Answer:', answer);
      }
    });
  }

  /**
   * Example: Delete a notebook
   */
  deleteNotebook(notebookId: string): void {
    if (!confirm('Are you sure you want to delete this notebook?')) {
      return;
    }

    this.notebookApi.deleteNotebook(notebookId, true).pipe(
      tap(() => {
        console.log('Deleted notebook:', notebookId);
      }),
      catchError(error => {
        this.error.set(error.message);
        return of(null);
      })
    ).subscribe(() => {
      // Remove from the list
      this.notebooks.update(notebooks => 
        notebooks.filter(n => n.id !== notebookId)
      );
    });
  }

  /**
   * Example: Add a text source to a notebook
   */
  addTextSource(notebookId: string, title: string, content: string): void {
    this.sourceApi.importTextSource({
      notebook_id: notebookId,
      title,
      content
    }).pipe(
      tap(source => {
        console.log('Added text source:', source);
      }),
      catchError(error => {
        this.error.set(error.message);
        return of(null);
      })
    ).subscribe(() => {
      // Reload sources for this notebook
      this.loadNotebookSources(notebookId);
    });
  }

  /**
   * Example: Generate a blog post
   */
  generateBlogPost(notebookId: string): void {
    this.notebookApi.generateBlogPost(notebookId, {
      title: 'Summary Blog Post',
      target_word_count: 550,
      tone: 'informative',
      include_references: true
    }).pipe(
      tap(output => {
        console.log('Generated blog post:', output);
        console.log('Word count:', output.word_count);
      }),
      catchError(error => {
        this.error.set(error.message);
        return of(null);
      })
    ).subscribe();
  }
}
