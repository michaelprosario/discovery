import { useCallback, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../api/client';
import { notebooksApi, sourcesApi } from '../api/services';
import { qk } from './queries';
import type { ArticleResult } from '../api/types';

export type BuildPhase = 'idle' | 'creating-notebook' | 'adding-sources' | 'done';

export interface AddedArticle {
  title: string;
  link: string;
  sourceId: string;
}

export interface FailedArticle {
  title: string;
  link: string;
  reason: string;
}

export interface BuildResult {
  notebookId: string;
  notebookName: string;
  added: AddedArticle[];
  failed: FailedArticle[];
  /** True when the user cancelled before every selected article was processed. */
  cancelled: boolean;
}

export interface RunParams {
  name: string;
  description?: string;
  tags?: string[];
  articles: ArticleResult[];
}

function messageOf(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return 'Unknown error';
}

function dedupeByLink(articles: ArticleResult[]): ArticleResult[] {
  const seen = new Set<string>();
  const out: ArticleResult[] = [];
  for (const a of articles) {
    if (!seen.has(a.link)) {
      seen.add(a.link);
      out.push(a);
    }
  }
  return out;
}

/**
 * Orchestrates "create a notebook from selected article-search results":
 * create the notebook (the gate), then import each selected article as a URL
 * source sequentially with per-item error isolation, building an added/failed
 * report. Supports mid-run cancellation (stops before the next item; an
 * in-flight import is allowed to finish server-side) and retrying just the
 * failures against the already-created notebook.
 */
export function useBuildNotebookFromArticles() {
  const queryClient = useQueryClient();
  const [phase, setPhase] = useState<BuildPhase>('idle');
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [result, setResult] = useState<BuildResult | null>(null);
  const [error, setError] = useState<unknown>(null);
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
    setError(null);
  }, []);

  /** Import a list of articles into an existing notebook, sequentially. */
  const importArticles = useCallback(
    async (notebookId: string, articles: ArticleResult[]) => {
      const added: AddedArticle[] = [];
      const failed: FailedArticle[] = [];
      setProgress({ current: 0, total: articles.length });
      setPhase('adding-sources');

      for (let i = 0; i < articles.length; i++) {
        if (cancelRef.current) {
          // Treat unprocessed remainder as failed-with-reason for the report.
          for (const a of articles.slice(i)) {
            failed.push({ title: a.title, link: a.link, reason: 'Cancelled' });
          }
          break;
        }
        const article = articles[i];
        setProgress({ current: i + 1, total: articles.length });
        try {
          const source = await sourcesApi.importUrl({
            notebook_id: notebookId,
            url: article.link,
            title: article.title || undefined,
          });
          added.push({ title: article.title, link: article.link, sourceId: source.id });
        } catch (err) {
          failed.push({ title: article.title, link: article.link, reason: messageOf(err) });
        }
      }
      return { added, failed };
    },
    [],
  );

  const run = useCallback(
    async (params: RunParams) => {
      setError(null);
      setResult(null);
      cancelRef.current = false;

      // Step 1 — create the notebook. This is the gate: if it fails, stop.
      setPhase('creating-notebook');
      let notebook;
      try {
        notebook = await notebooksApi.create({
          name: params.name.trim(),
          description: params.description?.trim() || undefined,
          tags: params.tags?.filter(Boolean),
        });
      } catch (err) {
        setError(err);
        setPhase('idle');
        return;
      }

      // Step 2 — import each selected article as a URL source.
      const articles = dedupeByLink(params.articles);
      const { added, failed } = await importArticles(notebook.id, articles);

      setResult({
        notebookId: notebook.id,
        notebookName: notebook.name,
        added,
        failed,
        cancelled: cancelRef.current,
      });
      setPhase('done');
      invalidate(notebook.id);
    },
    [importArticles, invalidate],
  );

  /** Re-attempt only the previously failed articles against the same notebook. */
  const retryFailed = useCallback(async () => {
    if (!result || result.failed.length === 0) return;
    cancelRef.current = false;
    const toRetry = result.failed.map((f) => ({ title: f.title, link: f.link }));
    const { added, failed } = await importArticles(result.notebookId, toRetry);

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
  }, [result, importArticles, invalidate]);

  return { phase, progress, result, error, run, cancel, reset, retryFailed };
}
