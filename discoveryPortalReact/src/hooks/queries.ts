import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  notebooksApi,
  outputsApi,
  sourcesApi,
  vectorApi,
  type ListNotebooksParams,
} from '../api/services';
import type {
  CreateNotebookRequest,
  GenerateBlogPostRequest,
  ImportFileSourceRequest,
  ImportTextSourceRequest,
  ImportUrlSourceRequest,
  UpdateNotebookRequest,
} from '../api/types';

// Centralised query keys so mutations can invalidate precisely.
export const qk = {
  notebooks: (params?: ListNotebooksParams) => ['notebooks', params ?? {}] as const,
  notebook: (id: string) => ['notebook', id] as const,
  sources: (notebookId: string) => ['sources', notebookId] as const,
  source: (id: string) => ['source', id] as const,
  outputs: (notebookId: string) => ['outputs', notebookId] as const,
  output: (id: string) => ['output', id] as const,
  vectorCount: (notebookId: string) => ['vectorCount', notebookId] as const,
};

// --- Notebooks --------------------------------------------------------------

export function useNotebooks(params: ListNotebooksParams = {}) {
  return useQuery({
    queryKey: qk.notebooks(params),
    queryFn: () => notebooksApi.list(params),
  });
}

export function useNotebook(id: string) {
  return useQuery({
    queryKey: qk.notebook(id),
    queryFn: () => notebooksApi.get(id),
    enabled: !!id,
  });
}

export function useCreateNotebook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateNotebookRequest) => notebooksApi.create(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notebooks'] }),
  });
}

export function useUpdateNotebook(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdateNotebookRequest) => notebooksApi.update(id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.notebook(id) });
      qc.invalidateQueries({ queryKey: ['notebooks'] });
    },
  });
}

export function useRenameNotebook(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (newName: string) => notebooksApi.rename(id, newName),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.notebook(id) });
      qc.invalidateQueries({ queryKey: ['notebooks'] });
    },
  });
}

export function useDeleteNotebook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => notebooksApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notebooks'] }),
  });
}

// --- Sources ----------------------------------------------------------------

export function useSources(notebookId: string) {
  return useQuery({
    queryKey: qk.sources(notebookId),
    queryFn: () => sourcesApi.listByNotebook(notebookId),
    enabled: !!notebookId,
  });
}

export function useSource(id: string) {
  return useQuery({
    queryKey: qk.source(id),
    queryFn: () => sourcesApi.get(id),
    enabled: !!id,
  });
}

function useInvalidateNotebookChildren(notebookId: string) {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: qk.sources(notebookId) });
    qc.invalidateQueries({ queryKey: qk.notebook(notebookId) });
  };
}

export function useImportFileSource(notebookId: string) {
  const invalidate = useInvalidateNotebookChildren(notebookId);
  return useMutation({
    mutationFn: (body: ImportFileSourceRequest) => sourcesApi.importFile(body),
    onSuccess: invalidate,
  });
}

export function useImportUrlSource(notebookId: string) {
  const invalidate = useInvalidateNotebookChildren(notebookId);
  return useMutation({
    mutationFn: (body: ImportUrlSourceRequest) => sourcesApi.importUrl(body),
    onSuccess: invalidate,
  });
}

export function useImportTextSource(notebookId: string) {
  const invalidate = useInvalidateNotebookChildren(notebookId);
  return useMutation({
    mutationFn: (body: ImportTextSourceRequest) => sourcesApi.importText(body),
    onSuccess: invalidate,
  });
}

export function useExtractContent(notebookId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, force }: { id: string; force?: boolean }) =>
      sourcesApi.extract(id, force),
    onSuccess: (src) => {
      qc.invalidateQueries({ queryKey: qk.sources(notebookId) });
      qc.invalidateQueries({ queryKey: qk.source(src.id) });
    },
  });
}

export function useDeleteSource(notebookId: string) {
  const invalidate = useInvalidateNotebookChildren(notebookId);
  return useMutation({
    mutationFn: (id: string) => sourcesApi.remove(id, notebookId),
    onSuccess: invalidate,
  });
}

// --- Outputs ----------------------------------------------------------------

export function useOutputs(notebookId: string) {
  return useQuery({
    queryKey: qk.outputs(notebookId),
    queryFn: () => outputsApi.listByNotebook(notebookId),
    enabled: !!notebookId,
  });
}

export function useOutput(id: string) {
  return useQuery({
    queryKey: qk.output(id),
    queryFn: () => outputsApi.get(id),
    enabled: !!id,
  });
}

export function useGenerateBlogPost(notebookId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: GenerateBlogPostRequest) =>
      notebooksApi.generateBlogPost(notebookId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.outputs(notebookId) });
      qc.invalidateQueries({ queryKey: qk.notebook(notebookId) });
    },
  });
}

export function useDeleteOutput(notebookId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => outputsApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.outputs(notebookId) });
      qc.invalidateQueries({ queryKey: qk.notebook(notebookId) });
    },
  });
}

// --- Vector indexing --------------------------------------------------------

export function useVectorCount(notebookId: string) {
  return useQuery({
    queryKey: qk.vectorCount(notebookId),
    queryFn: () => vectorApi.count(notebookId),
    enabled: !!notebookId,
    retry: false,
  });
}

export function useIngestNotebook(notebookId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (force: boolean) => vectorApi.ingest(notebookId, { force_reingest: force }),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.vectorCount(notebookId) }),
  });
}
