// Typed mirrors of the FastAPI DTOs (see src/api/dtos.py on the backend).
// Only the fields the front-end actually consumes are modelled.

// --- Auth -------------------------------------------------------------------

export interface User {
  id: string;
  email: string;
  display_name: string | null;
  roles: string[];
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name?: string;
}

// --- Notebooks --------------------------------------------------------------

export interface Notebook {
  id: string;
  name: string;
  description: string | null;
  tags: string[];
  source_count: number;
  output_count: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface NotebookListResponse {
  notebooks: Notebook[];
  total: number;
}

export interface CreateNotebookRequest {
  name: string;
  description?: string;
  tags?: string[];
}

export interface UpdateNotebookRequest {
  name?: string;
  description?: string;
  tags?: string[];
}

export type SortOrder = 'asc' | 'desc';

// --- Sources ----------------------------------------------------------------

export type SourceType = 'file' | 'url' | 'text';
export type FileType = 'pdf' | 'docx' | 'doc' | 'txt' | 'md';

export interface Source {
  id: string;
  notebook_id: string;
  name: string;
  source_type: SourceType;
  file_type: FileType | null;
  url: string | null;
  file_path: string | null;
  file_size: number | null;
  content_hash: string;
  extracted_text: string;
  metadata: Record<string, unknown>;
  created_by: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface SourceListResponse {
  sources: Source[];
  total: number;
}

export interface ImportFileSourceRequest {
  notebook_id: string;
  name: string;
  file_content: string; // base64
  file_type: FileType;
}

export interface ImportUrlSourceRequest {
  notebook_id: string;
  url: string;
  title?: string;
}

export interface ImportTextSourceRequest {
  notebook_id: string;
  title: string;
  content: string;
}

// --- Outputs ----------------------------------------------------------------

export type OutputType = 'blog_post' | 'summary' | 'outline' | 'qa_response' | string;
export type OutputStatus = 'draft' | 'in_progress' | 'completed' | 'failed' | string;

export interface Output {
  id: string;
  notebook_id: string;
  title: string;
  content: string;
  output_type: OutputType;
  status: OutputStatus;
  prompt: string | null;
  template_name: string | null;
  metadata: Record<string, unknown>;
  source_references: string[];
  word_count: number;
  created_by: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface OutputSummary {
  id: string;
  notebook_id: string;
  title: string;
  output_type: OutputType;
  status: OutputStatus;
  word_count: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface OutputListResponse {
  outputs: OutputSummary[];
  total: number;
}

export interface GenerateBlogPostRequest {
  title: string;
  prompt?: string;
  template_name?: string;
  target_word_count?: number;
  tone?: string;
  include_references?: boolean;
}

// --- Vector search / ingestion ---------------------------------------------

export interface IngestNotebookRequest {
  chunk_size?: number;
  overlap?: number;
  force_reingest?: boolean;
}

export interface IngestNotebookResponse {
  notebook_id: string;
  chunks_ingested: number;
  message: string;
}

export interface VectorCountResponse {
  notebook_id: string;
  vector_count: number;
}

// --- Q&A --------------------------------------------------------------------

export interface QaRequest {
  question: string;
  max_sources?: number;
  temperature?: number;
  max_tokens?: number;
}

export interface QaSourceItem {
  text: string;
  source_id: string | null;
  chunk_index: number;
  relevance_score: number;
  source_name: string | null;
  source_type: string | null;
}

export interface QaResponse {
  question: string;
  answer: string;
  sources: QaSourceItem[];
  notebook_id: string;
  confidence_score: number | null;
  processing_time_ms: number | null;
}

// --- Article search ---------------------------------------------------------

export interface ArticleSearchRequest {
  question: string;
  max_results?: number;
}

export interface ArticleResult {
  title: string;
  link: string;
}

export interface ArticleSearchResponse {
  robust_articles: ArticleResult[];
}
