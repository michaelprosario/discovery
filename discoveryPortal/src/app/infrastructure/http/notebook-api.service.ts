/**
 * Notebook API Service
 * Handles all notebook-related HTTP operations following clean architecture
 */

import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpClientService } from '../http/http-client.service';
import {
  NotebookResponse,
  NotebookListResponse,
  CreateNotebookRequest,
  UpdateNotebookRequest,
  RenameNotebookRequest,
  AddTagsRequest,
  RemoveTagsRequest,
  ListNotebooksParams,
  GenerateBlogPostRequest,
  OutputResponse
} from '../../core/models';

@Injectable({
  providedIn: 'root'
})
export class NotebookApiService {
  private httpClient = inject(HttpClientService);
  private readonly baseEndpoint = 'api/notebooks';

  /**
   * Create a new notebook
   */
  createNotebook(request: CreateNotebookRequest): Observable<NotebookResponse> {
    return this.httpClient.post<NotebookResponse>(this.baseEndpoint, request);
  }

  /**
   * Get a notebook by ID
   */
  getNotebook(notebookId: string): Observable<NotebookResponse> {
    return this.httpClient.get<NotebookResponse>(`${this.baseEndpoint}/${notebookId}`);
  }

  /**
   * List all notebooks with optional filtering and sorting
   */
  listNotebooks(params?: ListNotebooksParams): Observable<NotebookListResponse> {
    const queryParams: Record<string, string | number | boolean> = {};
    
    if (params) {
      if (params.tags && params.tags.length > 0) {
        queryParams['tags'] = params.tags.join(',');
      }
      if (params.sort_by) {
        queryParams['sort_by'] = params.sort_by;
      }
      if (params.sort_order) {
        queryParams['sort_order'] = params.sort_order;
      }
      if (params.limit !== undefined && params.limit !== null) {
        queryParams['limit'] = params.limit;
      }
      if (params.offset !== undefined) {
        queryParams['offset'] = params.offset;
      }
    }

    return this.httpClient.get<NotebookListResponse>(this.baseEndpoint, {
      params: queryParams
    });
  }

  /**
   * Update an existing notebook
   */
  updateNotebook(notebookId: string, request: UpdateNotebookRequest): Observable<NotebookResponse> {
    return this.httpClient.put<NotebookResponse>(`${this.baseEndpoint}/${notebookId}`, request);
  }

  /**
   * Delete a notebook
   */
  deleteNotebook(notebookId: string, cascade: boolean = false): Observable<void> {
    return this.httpClient.delete<void>(`${this.baseEndpoint}/${notebookId}`, {
      params: { cascade }
    });
  }

  /**
   * Rename a notebook
   */
  renameNotebook(notebookId: string, request: RenameNotebookRequest): Observable<NotebookResponse> {
    return this.httpClient.patch<NotebookResponse>(
      `${this.baseEndpoint}/${notebookId}/rename`,
      request
    );
  }

  /**
   * Add tags to a notebook
   */
  addTags(notebookId: string, request: AddTagsRequest): Observable<NotebookResponse> {
    return this.httpClient.post<NotebookResponse>(
      `${this.baseEndpoint}/${notebookId}/tags`,
      request
    );
  }

  /**
   * Remove tags from a notebook
   */
  removeTags(notebookId: string, request: RemoveTagsRequest): Observable<NotebookResponse> {
    return this.httpClient.delete<NotebookResponse>(
      `${this.baseEndpoint}/${notebookId}/tags`,
      { params: request as any }
    );
  }

  /**
   * Generate a blog post from notebook sources
   */
  generateBlogPost(
    notebookId: string,
    request: GenerateBlogPostRequest
  ): Observable<OutputResponse> {
    return this.httpClient.post<OutputResponse>(
      `${this.baseEndpoint}/${notebookId}/generate-blog-post`,
      request
    );
  }
}
