import { ApiError } from '../api/client';
import { sourcesApi } from '../api/services';
import type { ArticleResult } from '../api/types';

// Shared "import article-search results as URL sources" core, used by both
// `useBuildNotebookFromArticles` (create-then-add) and `useAddSourcesToNotebook`
// (add to an existing notebook). Keeping the sequential import loop in one place
// prevents the two flows from drifting.

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

export interface ImportProgress {
  current: number;
  total: number;
}

export function messageOf(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return 'Unknown error';
}

export function dedupeByLink(articles: ArticleResult[]): ArticleResult[] {
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
 * Import a list of articles into an existing notebook as URL sources,
 * sequentially, with per-item error isolation. The cancel check is consulted
 * between items (an in-flight import is allowed to finish server-side); any
 * unprocessed remainder is reported as failed with reason "Cancelled".
 */
export async function importArticlesSequential(
  notebookId: string,
  articles: ArticleResult[],
  opts: { isCancelled: () => boolean; onProgress: (p: ImportProgress) => void },
): Promise<{ added: AddedArticle[]; failed: FailedArticle[] }> {
  const added: AddedArticle[] = [];
  const failed: FailedArticle[] = [];
  const total = articles.length;
  opts.onProgress({ current: 0, total });

  for (let i = 0; i < articles.length; i++) {
    if (opts.isCancelled()) {
      for (const a of articles.slice(i)) {
        failed.push({ title: a.title, link: a.link, reason: 'Cancelled' });
      }
      break;
    }
    const article = articles[i];
    opts.onProgress({ current: i + 1, total });
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
}
