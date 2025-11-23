/**
 * Q&A API Service
 * Handles Q&A and RAG-related HTTP operations
 */

import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpClientService } from '../http/http-client.service';
import { AskQuestionRequest, QaResponse } from '../../core/models';

@Injectable({
  providedIn: 'root'
})
export class QaApiService {
  private httpClient = inject(HttpClientService);
  private readonly baseEndpoint = 'api/notebooks';

  /**
   * Ask a question about a notebook's content using RAG
   */
  askQuestion(notebookId: string, request: AskQuestionRequest): Observable<QaResponse> {
    return this.httpClient.post<QaResponse>(
      `${this.baseEndpoint}/${notebookId}/qa`,
      request
    );
  }
}
