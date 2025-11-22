/**
 * Notebook domain models
 * Generated from OpenAPI specification
 */

export interface NotebookResponse {
  id: string;
  name: string;
  description: string | null;
  tags: string[];
  source_count: number;
  output_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateNotebookRequest {
  name: string;
  description?: string | null;
  tags?: string[] | null;
}

export interface UpdateNotebookRequest {
  name?: string | null;
  description?: string | null;
  tags?: string[] | null;
}

export interface RenameNotebookRequest {
  new_name: string;
}

export interface AddTagsRequest {
  tags: string[];
}

export interface RemoveTagsRequest {
  tags: string[];
}

export interface NotebookListResponse {
  notebooks: NotebookResponse[];
  total: number;
}

export type SortOption = 'name' | 'created_at' | 'updated_at' | 'source_count';
export type SortOrder = 'asc' | 'desc';

export interface ListNotebooksParams {
  tags?: string[] | null;
  sort_by?: SortOption;
  sort_order?: SortOrder;
  limit?: number | null;
  offset?: number;
}
