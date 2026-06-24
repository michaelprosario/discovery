import { useMemo, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { articleApi } from '../../api/services';
import { useAddSourcesToNotebook } from '../../hooks/useAddSourcesToNotebook';
import { useIngestNotebook } from '../../hooks/queries';
import type { ArticleResult } from '../../api/types';
import { ErrorMessage } from '../../components/ErrorMessage';
import { IngestReport } from '../../components/IngestReport';
import styles from './AddSourcesFromSearch.module.css';

/**
 * Search the web for articles and add the selected ones as URL sources to the
 * notebook the user is reviewing. On completion, reports which articles were
 * added and which could not be ingested (with reasons), and offers a one-click
 * "Index for Q&A".
 */
export function AddSourcesFromSearch({ notebookId }: { notebookId: string }) {
  const [question, setQuestion] = useState('');
  const [maxResults, setMaxResults] = useState(10);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const add = useAddSourcesToNotebook();
  const ingest = useIngestNotebook(notebookId);

  const search = useMutation({
    mutationFn: () => articleApi.search({ question: question.trim(), max_results: maxResults }),
    onSuccess: (data) => {
      // Default to all results selected (de-duped by link).
      const seen = new Set<string>();
      const links = (data.robust_articles ?? [])
        .map((a) => a.link)
        .filter((l) => (seen.has(l) ? false : seen.add(l)));
      setSelected(new Set(links));
    },
  });

  // De-dupe results by link for display and selection.
  const articles: ArticleResult[] = useMemo(() => {
    const seen = new Set<string>();
    return (search.data?.robust_articles ?? []).filter((a) =>
      seen.has(a.link) ? false : seen.add(a.link),
    );
  }, [search.data]);

  const allSelected = selected.size === articles.length && articles.length > 0;

  function toggle(link: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(link)) next.delete(link);
      else next.add(link);
      return next;
    });
  }

  function toggleAll() {
    setSelected(allSelected ? new Set() : new Set(articles.map((a) => a.link)));
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    add.reset(); // clear any prior summary
    search.mutate();
  }

  function handleAdd() {
    const chosen = articles.filter((a) => selected.has(a.link));
    add.run({ notebookId, articles: chosen });
  }

  function handleAddMore() {
    add.reset();
    search.reset();
    setSelected(new Set());
  }

  // --- adding phase ---------------------------------------------------------
  if (add.phase === 'adding-sources') {
    return (
      <div className="card stack">
        <h3 style={{ margin: 0 }}>Adding sources…</h3>
        <div className="row">
          <div className="spinner" />
          <span>
            Adding source {add.progress.current} of {add.progress.total}…
          </span>
        </div>
        <div>
          <button className="btn btn-secondary" onClick={add.cancel}>
            Cancel
          </button>
        </div>
        <p className="text-sm muted" style={{ margin: 0 }}>
          Cancelling stops before the next article; any source already in progress will still
          finish.
        </p>
      </div>
    );
  }

  // --- summary phase --------------------------------------------------------
  if (add.phase === 'done' && add.result) {
    const { added, failed, cancelled } = add.result;
    const processed = added.length + failed.length;
    return (
      <div className="card stack">
        <h3 style={{ margin: 0 }}>
          {added.length} of {processed} article(s) added{cancelled ? ' (cancelled)' : ''}
        </h3>

        <IngestReport added={added} failed={failed} />

        <ErrorMessage error={ingest.error} />
        {ingest.isSuccess && ingest.data && (
          <div className="alert alert-success">{ingest.data.message}</div>
        )}

        <div className="row" style={{ flexWrap: 'wrap' }}>
          {added.length > 0 && (
            <button
              className="btn btn-secondary"
              onClick={() => ingest.mutate(false)}
              disabled={ingest.isPending || ingest.isSuccess}
            >
              {ingest.isPending ? 'Indexing…' : ingest.isSuccess ? 'Indexed ✓' : 'Index for Q&A'}
            </button>
          )}

          {failed.length > 0 && (
            <button className="btn btn-secondary" onClick={add.retryFailed}>
              Retry failed ({failed.length})
            </button>
          )}

          <button className="btn" onClick={handleAddMore}>
            Add more sources
          </button>
        </div>
      </div>
    );
  }

  // --- search + results phase (default) -------------------------------------
  return (
    <div className="stack">
      <div>
        <h3 style={{ margin: 0 }}>Find sources on the web</h3>
        <p className="muted text-sm" style={{ margin: '0.25rem 0 0' }}>
          Search for articles and add the ones you want as sources to this notebook.
        </p>
      </div>

      <form onSubmit={handleSearch} className="card">
        <div className="field">
          <label>Question or topic</label>
          <input
            className="input"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. How does retrieval-augmented generation work?"
            required
          />
        </div>
        <div className="row" style={{ alignItems: 'flex-end' }}>
          <div className="field" style={{ width: 160, marginBottom: 0 }}>
            <label>Max results</label>
            <input
              className="input"
              type="number"
              min={1}
              max={20}
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
            />
          </div>
          <button className="btn" type="submit" disabled={!question.trim() || search.isPending}>
            {search.isPending ? 'Searching…' : 'Search'}
          </button>
        </div>
      </form>

      <ErrorMessage error={search.error} />

      {search.isSuccess &&
        (articles.length === 0 ? (
          <div className="card">
            <p className="muted">No articles found.</p>
          </div>
        ) : (
          <div className="stack">
            <div className="row-between">
              <h3 style={{ margin: 0, fontSize: '1rem' }}>
                Results ({selected.size} of {articles.length} selected)
              </h3>
              <button className="btn btn-secondary btn-sm" onClick={toggleAll}>
                {allSelected ? 'Select none' : 'Select all'}
              </button>
            </div>

            <div>
              {articles.map((a) => (
                <label key={a.link} className={styles.articleRow}>
                  <input
                    type="checkbox"
                    checked={selected.has(a.link)}
                    onChange={() => toggle(a.link)}
                  />
                  <div className={styles.articleBody}>
                    <div className={styles.articleTitle}>{a.title}</div>
                    <span className={`muted ${styles.articleLink}`}>{a.link}</span>
                  </div>
                </label>
              ))}
            </div>

            <div className="row">
              <button className="btn" onClick={handleAdd} disabled={selected.size === 0}>
                Add sources to notebook
              </button>
            </div>
          </div>
        ))}
    </div>
  );
}
