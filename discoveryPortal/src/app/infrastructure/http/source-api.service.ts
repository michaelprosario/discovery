/**
 * Source API Service
 * Handles all source-related HTTP operations following clean architecture
 */

import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpClientService } from '../http/http-client.service';
import {
  SourceResponse,
  SourceListResponse,
  SourcePreviewResponse,
  ImportFileSourceRequest,
  ImportUrlSourceRequest,
  ImportTextSourceRequest,
  RenameSourceRequest,
  ExtractContentRequest,
  ListSourcesParams,
  AddSourcesBySearchRequest,
  AddSourcesBySearchResponse
} from '../../core/models';

@Injectable({
  providedIn: 'root'
})
export class SourceApiService {
  private httpClient = inject(HttpClientService);
  private readonly baseEndpoint = 'api/sources';

  /**
   * Import a file source into a notebook
   */
  importFileSource(request: ImportFileSourceRequest): Observable<SourceResponse> {
    return this.httpClient.post<SourceResponse>(`${this.baseEndpoint}/file`, request);
  }

  /**
   * Import a URL source into a notebook
   */
  importUrlSource(request: ImportUrlSourceRequest): Observable<SourceResponse> {
    return this.httpClient.post<SourceResponse>(`${this.baseEndpoint}/url`, request);
  }

  /**
   * Import a text source into a notebook
   */
  importTextSource(request: ImportTextSourceRequest): Observable<SourceResponse> {
    return this.httpClient.post<SourceResponse>(`${this.baseEndpoint}/text`, request);
  }

  /**
   * Get a source by ID
   */
  getSource(sourceId: string, includeDeleted: boolean = false): Observable<SourceResponse> {
    return this.httpClient.get<SourceResponse>(`${this.baseEndpoint}/${sourceId}`, {
      params: { include_deleted: includeDeleted }
    });
  }

  /**
   * List sources by notebook with optional filtering and sorting
   */
  listSourcesByNotebook(params: ListSourcesParams): Observable<SourceListResponse> {
    const { notebook_id, ...queryParams } = params;
    const filteredParams: Record<string, string | number | boolean> = {};

    Object.entries(queryParams).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        filteredParams[key] = value;
      }
    });

    return this.httpClient.get<SourceListResponse>(
      `${this.baseEndpoint}/notebook/${notebook_id}`,
      { params: filteredParams }
    );
  }

  /**
   * Delete a source (soft delete)
   */
  deleteSource(sourceId: string, notebookId: string): Observable<void> {
    return this.httpClient.delete<void>(`${this.baseEndpoint}/${sourceId}`, {
      params: { notebook_id: notebookId }
    });
  }

  /**
   * Rename a source
   */
  renameSource(sourceId: string, request: RenameSourceRequest): Observable<SourceResponse> {
    return this.httpClient.patch<SourceResponse>(
      `${this.baseEndpoint}/${sourceId}/rename`,
      request
    );
  }

  /**
   * Restore a soft-deleted source
   */
  restoreSource(sourceId: string, notebookId: string): Observable<SourceResponse> {
    return this.httpClient.post<SourceResponse>(
      `${this.baseEndpoint}/${sourceId}/restore`,
      {},
      { params: { notebook_id: notebookId } }
    );
  }

  /**
   * Extract content from a source
   */
  extractContent(sourceId: string, request: ExtractContentRequest): Observable<SourceResponse> {
    return this.httpClient.post<SourceResponse>(
      `${this.baseEndpoint}/${sourceId}/extract`,
      request
    );
  }

  /**
   * Get a preview of source content
   */
  getSourcePreview(sourceId: string, length: number = 500): Observable<SourcePreviewResponse> {
    return this.httpClient.get<SourcePreviewResponse>(
      `${this.baseEndpoint}/${sourceId}/preview`,
      { params: { length } }
    );
  }

  /**
   * Add sources to a notebook by searching for relevant articles
   */
  addSourcesBySearch(request: AddSourcesBySearchRequest): Observable<AddSourcesBySearchResponse> {
    return this.httpClient.post<AddSourcesBySearchResponse>(
      `${this.baseEndpoint}/search-and-add`,
      request
    );
  }
}
