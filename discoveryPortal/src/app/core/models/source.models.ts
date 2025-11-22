/**
 * Source domain models
 * Generated from OpenAPI specification
 */

export interface SourceResponse {
  id: string;
  notebook_id: string;
  name: string;
  source_type: string;
  file_type: string | null;
  url: string | null;
  file_path: string | null;
  file_size: number | null;
  content_hash: string;
  extracted_text: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface ImportFileSourceRequest {
  notebook_id: string;
  name: string;
  file_content: string; // Base64 encoded
  file_type: string; // pdf, docx, doc, txt, md
}

export interface ImportUrlSourceRequest {
  notebook_id: string;
  url: string;
  title?: string | null;
}

export interface ImportTextSourceRequest {
  notebook_id: string;
  title: string;
  content: string;
}

export interface RenameSourceRequest {
  new_name: string;
}

export interface ExtractContentRequest {
  force?: boolean;
}

export interface SourceListResponse {
  sources: SourceResponse[];
  total: number;
}

export interface SourcePreviewResponse {
  id: string;
  name: string;
  preview: string;
  full_text_length: number;
}

export interface ListSourcesParams {
  notebook_id: string;
  include_deleted?: boolean;
  source_type?: string | null;
  file_type?: string | null;
  sort_by?: 'name' | 'created_at' | 'updated_at';
  sort_order?: 'asc' | 'desc';
  limit?: number | null;
  offset?: number;
}

export interface AddSourcesBySearchRequest {
  notebook_id: string;
  search_phrase: string;
  max_results?: number;
}

export interface AddSourcesBySearchResult {
  title: string;
  url: string;
  source_id: string | null;
  success: boolean;
  error: string | null;
}

export interface AddSourcesBySearchResponse {
  notebook_id: string;
  search_phrase: string;
  results: AddSourcesBySearchResult[];
  total_found: number;
  total_added: number;
}
