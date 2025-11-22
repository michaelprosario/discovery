/**
 * Output domain models
 * Generated from OpenAPI specification
 */

export type OutputType = 
  | 'summary'
  | 'blog_post'
  | 'briefing'
  | 'report'
  | 'essay'
  | 'faq'
  | 'meeting_notes'
  | 'comparative_analysis'
  | 'custom';

export type OutputStatus = 'draft' | 'generating' | 'completed' | 'failed';

export interface OutputResponse {
  id: string;
  notebook_id: string;
  title: string;
  content: string;
  output_type: string;
  status: string;
  prompt: string | null;
  template_name: string | null;
  metadata: Record<string, unknown>;
  source_references: string[];
  word_count: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface OutputSummaryResponse {
  id: string;
  notebook_id: string;
  title: string;
  output_type: string;
  status: string;
  word_count: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface CreateOutputRequest {
  title: string;
  output_type?: string;
  prompt?: string | null;
  template_name?: string | null;
}

export interface UpdateOutputRequest {
  title?: string | null;
  content?: string | null;
}

export interface OutputListResponse {
  outputs: OutputSummaryResponse[];
  total: number;
}

export interface OutputPreviewResponse {
  id: string;
  title: string;
  preview: string;
  full_content_length: number;
  word_count: number;
}

export interface ListOutputsParams {
  notebook_id?: string | null;
  output_type?: OutputType | null;
  status?: OutputStatus | null;
  sort_by?: 'name' | 'created_at' | 'updated_at';
  sort_order?: 'asc' | 'desc';
  limit?: number | null;
  offset?: number;
}

export interface SearchOutputsParams {
  q: string;
  notebook_id?: string | null;
  output_type?: OutputType | null;
  status?: OutputStatus | null;
  sort_by?: 'name' | 'created_at' | 'updated_at';
  sort_order?: 'asc' | 'desc';
  limit?: number | null;
  offset?: number;
}

export interface GenerateBlogPostRequest {
  title: string;
  prompt?: string | null;
  template_name?: string | null;
  target_word_count?: number;
  tone?: string;
  include_references?: boolean;
}
