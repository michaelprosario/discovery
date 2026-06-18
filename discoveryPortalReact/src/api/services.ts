import { api, request } from './client';
import { setTokens } from './tokenStore';
import type {
  ArticleSearchRequest,
  ArticleSearchResponse,
  CreateNotebookRequest,
  GenerateBlogPostRequest,
  ImportFileSourceRequest,
  ImportTextSourceRequest,
  ImportUrlSourceRequest,
  IngestNotebookRequest,
  IngestNotebookResponse,
  Notebook,
  NotebookListResponse,
  Output,
  OutputListResponse,
  QaRequest,
  QaResponse,
  RegisterRequest,
  Source,
  SourceListResponse,
  SortOrder,
  TokenResponse,
  UpdateNotebookRequest,
  User,
  VectorCountResponse,
} from './types';

// --- Auth -------------------------------------------------------------------

export const authApi = {
  /** OAuth2 password grant — `username` is the user's email. */
  async login(email: string, password: string): Promise<TokenResponse> {
    const form = new URLSearchParams();
    form.set('username', email);
    form.set('password', password);
    const tokens = await request<TokenResponse>('/api/auth/token', {
      method: 'POST',
      rawBody: form,
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      skipAuth: true,
    });
    setTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
    return tokens;
  },

  register(body: RegisterRequest): Promise<User> {
    return request<User>('/api/auth/register', { method: 'POST', body, skipAuth: true });
  },

  me(): Promise<User> {
    return api.get<User>('/api/auth/me');
  },

  logout(refreshToken: string): Promise<null> {
    return api.post<null>('/api/auth/logout', { refresh_token: refreshToken });
  },
};

// --- Notebooks --------------------------------------------------------------

export interface ListNotebooksParams {
  sortBy?: 'created_at' | 'updated_at' | 'name';
  sortOrder?: SortOrder;
}

export const notebooksApi = {
  list(params: ListNotebooksParams = {}): Promise<NotebookListResponse> {
    const q = new URLSearchParams();
    if (params.sortBy) q.set('sort_by', params.sortBy);
    if (params.sortOrder) q.set('sort_order', params.sortOrder);
    const qs = q.toString();
    return api.get<NotebookListResponse>(`/api/notebooks${qs ? `?${qs}` : ''}`);
  },

  get(id: string): Promise<Notebook> {
    return api.get<Notebook>(`/api/notebooks/${id}`);
  },

  create(body: CreateNotebookRequest): Promise<Notebook> {
    return api.post<Notebook>('/api/notebooks', body);
  },

  update(id: string, body: UpdateNotebookRequest): Promise<Notebook> {
    return api.put<Notebook>(`/api/notebooks/${id}`, body);
  },

  rename(id: string, newName: string): Promise<Notebook> {
    return api.patch<Notebook>(`/api/notebooks/${id}/rename`, { new_name: newName });
  },

  remove(id: string, cascade = true): Promise<null> {
    return api.delete<null>(`/api/notebooks/${id}?cascade=${cascade}`);
  },

  generateBlogPost(id: string, body: GenerateBlogPostRequest): Promise<Output> {
    return api.post<Output>(`/api/notebooks/${id}/generate-blog-post`, body);
  },
};

// --- Sources ----------------------------------------------------------------

export const sourcesApi = {
  listByNotebook(notebookId: string): Promise<SourceListResponse> {
    return api.get<SourceListResponse>(`/api/sources/notebook/${notebookId}`);
  },

  get(id: string): Promise<Source> {
    return api.get<Source>(`/api/sources/${id}`);
  },

  importFile(body: ImportFileSourceRequest): Promise<Source> {
    return api.post<Source>('/api/sources/file', body);
  },

  importUrl(body: ImportUrlSourceRequest): Promise<Source> {
    return api.post<Source>('/api/sources/url', body);
  },

  importText(body: ImportTextSourceRequest): Promise<Source> {
    return api.post<Source>('/api/sources/text', body);
  },

  extract(id: string, force = false): Promise<Source> {
    return api.post<Source>(`/api/sources/${id}/extract`, { force });
  },

  remove(id: string, notebookId: string): Promise<null> {
    return api.delete<null>(`/api/sources/${id}?notebook_id=${notebookId}`);
  },
};

// --- Outputs ----------------------------------------------------------------

export const outputsApi = {
  listByNotebook(notebookId: string): Promise<OutputListResponse> {
    return api.get<OutputListResponse>(`/api/outputs?notebook_id=${notebookId}`);
  },

  get(id: string): Promise<Output> {
    return api.get<Output>(`/api/outputs/${id}`);
  },

  remove(id: string): Promise<null> {
    return api.delete<null>(`/api/outputs/${id}`);
  },
};

// --- Vector search / indexing ----------------------------------------------

export const vectorApi = {
  ingest(notebookId: string, body: IngestNotebookRequest = {}): Promise<IngestNotebookResponse> {
    return api.post<IngestNotebookResponse>(`/api/notebooks/${notebookId}/ingest`, body);
  },

  count(notebookId: string): Promise<VectorCountResponse> {
    return api.get<VectorCountResponse>(`/api/notebooks/${notebookId}/vectors/count`);
  },
};

// --- Q&A --------------------------------------------------------------------

export const qaApi = {
  ask(notebookId: string, body: QaRequest): Promise<QaResponse> {
    return api.post<QaResponse>(`/api/notebooks/${notebookId}/qa`, body);
  },
};

// --- Article search ---------------------------------------------------------

export const articleApi = {
  search(body: ArticleSearchRequest): Promise<ArticleSearchResponse> {
    // Note: article search lives at /articles (no /api prefix) on the backend.
    return api.post<ArticleSearchResponse>('/articles/search', body);
  },
};
