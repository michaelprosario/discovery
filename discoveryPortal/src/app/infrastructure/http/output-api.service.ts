/**
 * Output API Service
 * Handles all output-related HTTP operations following clean architecture
 */

import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpClientService } from '../http/http-client.service';
import {
  OutputResponse,
  OutputListResponse,
  OutputPreviewResponse,
  CreateOutputRequest,
  UpdateOutputRequest,
  ListOutputsParams,
  SearchOutputsParams
} from '../../core/models';

@Injectable({
  providedIn: 'root'
})
export class OutputApiService {
  private httpClient = inject(HttpClientService);
  private readonly baseEndpoint = 'api/outputs';

  /**
   * Create a new output
   */
  createOutput(notebookId: string, request: CreateOutputRequest): Observable<OutputResponse> {
    return this.httpClient.post<OutputResponse>(this.baseEndpoint, request, {
      params: { notebook_id: notebookId }
    });
  }

  /**
   * Get an output by ID
   */
  getOutput(outputId: string): Observable<OutputResponse> {
    return this.httpClient.get<OutputResponse>(`${this.baseEndpoint}/${outputId}`);
  }

  /**
   * List outputs with optional filtering and sorting
   */
  listOutputs(params?: ListOutputsParams): Observable<OutputListResponse> {
    const queryParams: Record<string, string | number | boolean> = {};

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams[key] = value;
        }
      });
    }

    return this.httpClient.get<OutputListResponse>(this.baseEndpoint, {
      params: queryParams
    });
  }

  /**
   * Update an existing output
   */
  updateOutput(outputId: string, request: UpdateOutputRequest): Observable<OutputResponse> {
    return this.httpClient.put<OutputResponse>(`${this.baseEndpoint}/${outputId}`, request);
  }

  /**
   * Delete an output
   */
  deleteOutput(outputId: string): Observable<void> {
    return this.httpClient.delete<void>(`${this.baseEndpoint}/${outputId}`);
  }

  /**
   * Search outputs by content or title
   */
  searchOutputs(params: SearchOutputsParams): Observable<OutputListResponse> {
    const queryParams: Record<string, string | number | boolean> = {};

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams[key] = value;
      }
    });

    return this.httpClient.get<OutputListResponse>(`${this.baseEndpoint}/search`, {
      params: queryParams
    });
  }

  /**
   * Get a preview of output content
   */
  getOutputPreview(outputId: string, length: number = 300): Observable<OutputPreviewResponse> {
    return this.httpClient.get<OutputPreviewResponse>(
      `${this.baseEndpoint}/${outputId}/preview`,
      { params: { length } }
    );
  }
}
