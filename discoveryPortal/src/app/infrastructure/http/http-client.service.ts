/**
 * Base HTTP Client Service
 * Provides a foundation for all API service implementations with error handling
 */

import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { ApiConfigService } from '../config/api-config.service';
import { ErrorResponse, ValidationErrorResponse, AppResult } from '../../core/models';

export interface HttpOptions {
  headers?: HttpHeaders | { [header: string]: string | string[] };
  params?: HttpParams | { [param: string]: string | number | boolean | ReadonlyArray<string | number | boolean> };
  observe?: 'body';
  reportProgress?: boolean;
  responseType?: 'json';
  withCredentials?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class HttpClientService {
  private http = inject(HttpClient);
  private config = inject(ApiConfigService);

  /**
   * Perform GET request
   */
  get<T>(endpoint: string, options?: HttpOptions): Observable<T> {
    const url = this.buildUrl(endpoint);
    return this.http.get<T>(url, options).pipe(
      catchError((error) => this.handleError(error))
    );
  }

  /**
   * Perform POST request
   */
  post<T>(endpoint: string, body: unknown, options?: HttpOptions): Observable<T> {
    const url = this.buildUrl(endpoint);
    return this.http.post<T>(url, body, options).pipe(
      catchError((error) => this.handleError(error))
    );
  }

  /**
   * Perform PUT request
   */
  put<T>(endpoint: string, body: unknown, options?: HttpOptions): Observable<T> {
    const url = this.buildUrl(endpoint);
    return this.http.put<T>(url, body, options).pipe(
      catchError((error) => this.handleError(error))
    );
  }

  /**
   * Perform PATCH request
   */
  patch<T>(endpoint: string, body: unknown, options?: HttpOptions): Observable<T> {
    const url = this.buildUrl(endpoint);
    return this.http.patch<T>(url, body, options).pipe(
      catchError((error) => this.handleError(error))
    );
  }

  /**
   * Perform DELETE request
   */
  delete<T>(endpoint: string, options?: HttpOptions): Observable<T> {
    const url = this.buildUrl(endpoint);
    return this.http.delete<T>(url, options).pipe(
      catchError((error) => this.handleError(error))
    );
  }

  /**
   * Build full URL from endpoint
   */
  private buildUrl(endpoint: string): string {
    const baseUrl = this.config.getBaseUrl();
    
    // Remove leading slash from endpoint if present
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
    
    // If baseUrl is empty, return endpoint as-is (relative URL)
    if (!baseUrl) {
      return `/${cleanEndpoint}`;
    }
    
    // Remove trailing slash from baseUrl if present
    const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
    
    return `${cleanBaseUrl}/${cleanEndpoint}`;
  }

  /**
   * Handle HTTP errors
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An unknown error occurred';
    let validationErrors: ValidationErrorResponse | undefined;

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Client Error: ${error.error.message}`;
    } else {
      // Server-side error
      if (error.error) {
        if (this.isValidationErrorResponse(error.error)) {
          validationErrors = error.error;
          errorMessage = error.error.error;
        } else if (this.isErrorResponse(error.error)) {
          errorMessage = error.error.error;
        } else if (typeof error.error === 'string') {
          errorMessage = error.error;
        } else {
          errorMessage = `Server Error: ${error.status} ${error.statusText}`;
        }
      } else {
        errorMessage = `Server Error: ${error.status} ${error.statusText}`;
      }
    }

    const enhancedError = {
      message: errorMessage,
      status: error.status,
      statusText: error.statusText,
      validationErrors,
      originalError: error
    };

    return throwError(() => enhancedError);
  }

  /**
   * Type guard for ErrorResponse
   */
  private isErrorResponse(obj: unknown): obj is ErrorResponse {
    return (
      typeof obj === 'object' &&
      obj !== null &&
      'error' in obj &&
      typeof (obj as ErrorResponse).error === 'string'
    );
  }

  /**
   * Type guard for ValidationErrorResponse
   */
  private isValidationErrorResponse(obj: unknown): obj is ValidationErrorResponse {
    return (
      typeof obj === 'object' &&
      obj !== null &&
      'error' in obj &&
      'validation_errors' in obj &&
      Array.isArray((obj as ValidationErrorResponse).validation_errors)
    );
  }

  /**
   * Convert observable to AppResult pattern
   */
  toAppResult<T>(observable: Observable<T>): Observable<AppResult<T>> {
    return observable.pipe(
      map(data => ({
        success: true,
        data
      })),
      catchError(error => {
        return throwError(() => ({
          success: false,
          error: error.message,
          validationErrors: error.validationErrors
        }));
      })
    );
  }
}
