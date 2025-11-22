/**
 * Vector Search API Service
 * Handles all vector search and RAG-related HTTP operations following clean architecture
 */

import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpClientService } from '../http/http-client.service';
import {
  IngestNotebookRequest,
  IngestNotebookResponse,
  CreateCollectionRequest,
  CreateCollectionResponse,
  SimilaritySearchResponse,
  VectorCountResponse,
  QaResponse,
  AskQuestionRequest,
  QaHealthResponse,
  MindMapResponse,
  GenerateMindMapRequest
} from '../../core/models';

@Injectable({
  providedIn: 'root'
})
export class VectorSearchApiService {
  private httpClient = inject(HttpClientService);

  /**
   * Ingest a notebook and its sources into the vector database
   */
  ingestNotebook(
    notebookId: string,
    request?: IngestNotebookRequest
  ): Observable<IngestNotebookResponse> {
    const defaultRequest: IngestNotebookRequest = {
      chunk_size: 1000,
      overlap: 200,
      force_reingest: false,
      ...request
    };

    return this.httpClient.post<IngestNotebookResponse>(
      `api/notebooks/${notebookId}/ingest`,
      defaultRequest
    );
  }

  /**
   * Search for similar content within a notebook using semantic similarity
   */
  searchSimilarContent(
    notebookId: string,
    query: string,
    limit: number = 10
  ): Observable<SimilaritySearchResponse> {
    return this.httpClient.get<SimilaritySearchResponse>(
      `api/notebooks/${notebookId}/similar`,
      { params: { query, limit } }
    );
  }

  /**
   * Get the count of vectors stored for a notebook
   */
  getVectorCount(notebookId: string): Observable<VectorCountResponse> {
    return this.httpClient.get<VectorCountResponse>(
      `api/notebooks/${notebookId}/vectors/count`
    );
  }

  /**
   * Delete all vectors associated with a notebook
   */
  deleteNotebookVectors(notebookId: string): Observable<void> {
    return this.httpClient.delete<void>(`api/notebooks/${notebookId}/vectors`);
  }

  /**
   * Create a vector collection for a notebook
   */
  createCollection(
    notebookId: string,
    request?: CreateCollectionRequest
  ): Observable<CreateCollectionResponse> {
    return this.httpClient.post<CreateCollectionResponse>(
      `api/notebooks/${notebookId}/collection`,
      request || {}
    );
  }

  /**
   * Ask a question about notebook content using RAG
   */
  askQuestion(notebookId: string, request: AskQuestionRequest): Observable<QaResponse> {
    return this.httpClient.post<QaResponse>(`api/notebooks/${notebookId}/qa`, request);
  }

  /**
   * Get health status of the QA service
   */
  getQaHealth(): Observable<QaHealthResponse> {
    return this.httpClient.get<QaHealthResponse>('api/notebooks/qa/health');
  }

  /**
   * Generate a mind map outline from notebook content using RAG
   */
  generateMindMap(notebookId: string, request: GenerateMindMapRequest): Observable<MindMapResponse> {
    return this.httpClient.post<MindMapResponse>(
      `api/notebooks/${notebookId}/mindmap`,
      request
    );
  }

  /**
   * Get the mind map viewer HTML page for a notebook
   */
  getMindMapViewer(notebookId: string): Observable<string> {
    return this.httpClient.get<string>(`api/notebooks/${notebookId}/mindmap/viewer`, {
      responseType: 'text' as any
    });
  }
}
