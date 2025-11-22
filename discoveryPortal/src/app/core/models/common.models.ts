/**
 * Common domain models
 * Generated from OpenAPI specification
 */

export interface ErrorResponse {
  error: string;
  details?: Record<string, unknown> | null;
}

export interface ValidationErrorDetail {
  field: string;
  message: string;
  code?: string | null;
}

export interface ValidationErrorResponse {
  error: string;
  validation_errors: ValidationErrorDetail[];
}

export interface ArticleResponse {
  title: string;
  link: string;
}

export interface ArticleSearchRequest {
  question: string;
  max_results?: number;
}

export interface ArticleSearchResponse {
  robust_articles: ArticleResponse[];
}

/**
 * Result wrapper for service operations
 */
export interface AppResult<T> {
  success: boolean;
  data?: T;
  error?: string;
  validationErrors?: ValidationErrorDetail[];
}

/**
 * HTTP response wrapper
 */
export interface ApiResponse<T> {
  data: T;
  status: number;
  statusText: string;
}
