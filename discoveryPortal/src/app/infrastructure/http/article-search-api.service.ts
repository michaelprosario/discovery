/**
 * Article Search API Service
 * Handles article search operations
 */

import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpClientService } from '../http/http-client.service';
import { ArticleSearchRequest, ArticleSearchResponse } from '../../core/models';

@Injectable({
  providedIn: 'root'
})
export class ArticleSearchApiService {
  private httpClient = inject(HttpClientService);

  /**
   * Search for high-quality blog articles that answer a specific question
   */
  searchArticles(request: ArticleSearchRequest): Observable<ArticleSearchResponse> {
    return this.httpClient.post<ArticleSearchResponse>('articles/search', request);
  }
}
