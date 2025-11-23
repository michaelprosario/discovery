/**
 * Mind Map API Service
 * Handles all mind map-related HTTP operations
 */

import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpClientService } from './http-client.service';
import {
  GenerateMindMapRequest,
  MindMapResponse
} from '../../core/models';

@Injectable({
  providedIn: 'root'
})
export class MindMapApiService {
  private httpClient = inject(HttpClientService);
  private readonly baseEndpoint = 'api/notebooks';

  /**
   * Generate a mind map from notebook content using RAG
   */
  generateMindMap(notebookId: string, request: GenerateMindMapRequest): Observable<MindMapResponse> {
    return this.httpClient.post<MindMapResponse>(
      `${this.baseEndpoint}/${notebookId}/mindmap`,
      request
    );
  }

  /**
   * Get the mind map viewer URL for a notebook
   */
  getMindMapViewerUrl(notebookId: string): string {
    // Build the URL using the same pattern as other endpoints
    // The ApiConfigService will handle the base URL
    return `/api/notebooks/${notebookId}/mindmap/viewer`;
  }
}
