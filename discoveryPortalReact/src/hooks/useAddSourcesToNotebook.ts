import { useCallback, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { qk } from './queries';
import {
  dedupeByLink,
  importArticlesSequential,
  type AddedArticle,
  type FailedArticle,
  type ImportProgress,
} from './articleIngest';
import type { ArticleResult } from '../api/types';

export type { AddedArticle, FailedArticle };

export type AddSourcesPhase = 'idle' | 'adding-sources' | 'done';

export interface AddSourcesResult {
  notebookId: string;
  added: AddedArticle[];
  failed: FailedArticle[];
  /** True when the user cancelled before every selected article was processed. */
  cancelled: boolean;
}

export interface AddSourcesRunParams {
  notebookId: string;
  articles: ArticleResult[];
}

/**
 * Orchestrates "add selected article-search results to an existing notebook":
 * import each selected article as a URL source sequentially with per-item error
 * isolation, building an added/failed report. Supports mid-run cancellation and
 * retrying just the failures against the same notebook.
 *
 * Unlike `useBuildNotebookFromArticles`, there is no notebook-creation gate —
 * the notebook already exists, so import begins immediately on `run`.
 */
export function useAddSourcesToNotebook() {
  const queryClient = useQueryClient();
  const [phase, setPhase] = useState<AddSourcesPhase>('idle');
  const [progress, setProgress] = useState<ImportProgress>({ current: 0, total: 0 });
  const [result, setResult] = useState<AddSourcesResult | null>(null);
  const cancelRef = useRef(false);

  const invalidate = useCallback(
    (notebookId: string) => {
      queryClient.invalidateQueries({ queryKey: ['notebooks'] });
      queryClient.invalidateQueries({ queryKey: qk.notebook(notebookId) });
      queryClient.invalidateQueries({ queryKey: qk.sources(notebookId) });
      queryClient.invalidateQueries({ queryKey: qk.vectorCount(notebookId) });
    },
    [queryClient],
  );

  const cancel = useCallback(() => {
    cancelRef.current = true;
  }, []);

  const reset = useCallback(() => {
    cancelRef.current = false;
    setPhase('idle');
    setProgress({ current: 0, total: 0 });
    setResult(null);
  }, []);

  const importInto = useCallback((notebookId: string, articles: ArticleResult[]) => {
    setPhase('adding-sources');
    return importArticlesSequential(notebookId, articles, {
      isCancelled: () => cancelRef.current,
      onProgress: setProgress,
    });
  }, []);

  const run = useCallback(
    async ({ notebookId, articles }: AddSourcesRunParams) => {
      cancelRef.current = false;
      setResult(null);
      const { added, failed } = await importInto(notebookId, dedupeByLink(articles));
      setResult({ notebookId, added, failed, cancelled: cancelRef.current });
      setPhase('done');
      invalidate(notebookId);
    },
    [importInto, invalidate],
  );

  /** Re-attempt only the previously failed articles against the same notebook. */
  const retryFailed = useCallback(async () => {
    if (!result || result.failed.length === 0) return;
    cancelRef.current = false;
    const toRetry = result.failed.map((f) => ({ title: f.title, link: f.link }));
    const { added, failed } = await importInto(result.notebookId, toRetry);
    setResult((prev) =>
      prev
        ? {
            ...prev,
            added: [...prev.added, ...added],
            failed,
            cancelled: cancelRef.current,
          }
        : prev,
    );
    setPhase('done');
    invalidate(result.notebookId);
  }, [result, importInto, invalidate]);

  return { phase, progress, result, run, cancel, reset, retryFailed };
}
