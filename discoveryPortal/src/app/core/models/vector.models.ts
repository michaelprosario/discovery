/**
 * Vector search and RAG domain models
 * Generated from OpenAPI specification
 */

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

export interface CreateCollectionRequest {
  // Empty for now
}

export interface CreateCollectionResponse {
  notebook_id: string;
  collection_name: string;
  message: string;
  created: boolean;
}

export interface SimilaritySearchResultItem {
  text: string;
  source_id: string | null;
  chunk_index: number;
  distance: number | null;
  certainty: number | null;
  source_name: string | null;
}

export interface SimilaritySearchResponse {
  query: string;
  results: SimilaritySearchResultItem[];
  total: number;
}

export interface VectorCountResponse {
  notebook_id: string;
  vector_count: number;
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

export interface AskQuestionRequest {
  question: string;
  max_sources?: number;
  temperature?: number;
  max_tokens?: number;
}

export interface QaHealthResponse {
  status: string;
  llm_model: string;
  vector_db_status: string;
}

export interface MindMapSourceItem {
  text: string;
  source_id: string | null;
  chunk_index: number;
  relevance_score: number;
  source_name: string | null;
  source_type: string | null;
}

export interface MindMapResponse {
  prompt: string;
  markdown_outline: string;
  sources: MindMapSourceItem[];
  notebook_id: string;
  confidence_score: number | null;
  processing_time_ms: number | null;
}

export interface GenerateMindMapRequest {
  prompt: string;
  max_sources?: number;
  temperature?: number | null;
  max_tokens?: number | null;
}
