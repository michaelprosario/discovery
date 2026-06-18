import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBuildNotebookFromArticles } from '../../hooks/useBuildNotebookFromArticles';
import { useDeleteNotebook, useIngestNotebook } from '../../hooks/queries';
import type { ArticleResult } from '../../api/types';
import { ErrorMessage } from '../../components/ErrorMessage';
import styles from './CreateNotebookFromResults.module.css';

interface Props {
  /** The articles currently shown in the search results. */
  articles: ArticleResult[];
  /** The search question — used to prefill the notebook name/description. */
  question: string;
  /** Return to the plain results list. */
  onClose: () => void;
}

export function CreateNotebookFromResults({ articles, question, onClose }: Props) {
  const navigate = useNavigate();
  const build = useBuildNotebookFromArticles();

  // De-dupe by link for display (and selection) up front.
  const displayArticles = useMemo(() => {
    const seen = new Set<string>();
    return articles.filter((a) => (seen.has(a.link) ? false : seen.add(a.link)));
  }, [articles]);

  const [selected, setSelected] = useState<Set<string>>(
    () => new Set(displayArticles.map((a) => a.link)),
  );
  const [name, setName] = useState(() => question.trim().slice(0, 255));
  const [description, setDescription] = useState(
    () => `Created from article search: "${question.trim()}"`.slice(0, 2000),
  );
  const [tags, setTags] = useState('');

  const allSelected = selected.size === displayArticles.length && displayArticles.length > 0;

  function toggle(link: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(link)) next.delete(link);
      else next.add(link);
      return next;
    });
  }

  function toggleAll() {
    setSelected(allSelected ? new Set() : new Set(displayArticles.map((a) => a.link)));
  }

  function handleCreate() {
    const chosen = displayArticles.filter((a) => selected.has(a.link));
    build.run({
      name,
      description,
      tags: tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
      articles: chosen,
    });
  }

  // --- Summary actions (notebook already exists) ----------------------------
  const ingest = useIngestNotebook(build.result?.notebookId ?? '');
  const del = useDeleteNotebook();

  async function handleDeleteEmpty() {
    if (!build.result) return;
    if (!confirm('Delete the empty notebook?')) return;
    await del.mutateAsync(build.result.notebookId);
    build.reset();
    onClose();
  }

  // --- creating / adding phase ----------------------------------------------
  if (build.phase === 'creating-notebook' || build.phase === 'adding-sources') {
    return (
      <div className="card stack">
        <h2>Creating notebook…</h2>
        <div className="row">
          <div className="spinner" />
          <span>
            {build.phase === 'creating-notebook'
              ? 'Creating notebook record…'
              : `Adding source ${build.progress.current} of ${build.progress.total}…`}
          </span>
        </div>
        <div>
          <button className="btn btn-secondary" onClick={build.cancel}>
            Cancel
          </button>
        </div>
        <p className="text-sm muted" style={{ margin: 0 }}>
          Cancelling stops before the next article; any source already in progress will still finish.
        </p>
      </div>
    );
  }

  // --- summary phase --------------------------------------------------------
  if (build.phase === 'done' && build.result) {
    const { added, failed, cancelled, notebookId } = build.result;
    const processed = added.length + failed.length;
    return (
      <div className="stack">
        <div className="card stack">
          <h2>
            Notebook created — {added.length} of {processed} article(s) added
            {cancelled ? ' (cancelled)' : ''}
          </h2>

          {added.length > 0 && (
            <div>
              <h3 style={{ fontSize: '1rem' }}>✅ Added with no issues</h3>
              {added.map((a) => (
                <div key={a.link} className={`${styles.reportItem} ${styles.added}`}>
                  <div style={{ fontWeight: 600 }}>{a.title}</div>
                  <a href={a.link} target="_blank" rel="noreferrer" className={styles.articleLink}>
                    {a.link}
                  </a>
                </div>
              ))}
            </div>
          )}

          {failed.length > 0 && (
            <div>
              <h3 style={{ fontSize: '1rem' }}>⚠️ Could not be ingested</h3>
              {failed.map((f) => (
                <div key={f.link} className={`${styles.reportItem} ${styles.failed}`}>
                  <div style={{ fontWeight: 600 }}>{f.title}</div>
                  <a href={f.link} target="_blank" rel="noreferrer" className={styles.articleLink}>
                    {f.link}
                  </a>
                  <div className={styles.reason}>Reason: {f.reason}</div>
                </div>
              ))}
            </div>
          )}

          <ErrorMessage error={ingest.error || del.error} />
          {ingest.isSuccess && ingest.data && (
            <div className="alert alert-success">{ingest.data.message}</div>
          )}

          <div className="row" style={{ flexWrap: 'wrap' }}>
            <button className="btn" onClick={() => navigate(`/notebooks/${notebookId}`)}>
              Open notebook
            </button>

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
              <button
                className="btn btn-secondary"
                onClick={build.retryFailed}
                disabled={del.isPending}
              >
                Retry failed ({failed.length})
              </button>
            )}

            {added.length === 0 && (
              <button
                className="btn btn-danger"
                onClick={handleDeleteEmpty}
                disabled={del.isPending}
              >
                {del.isPending ? 'Deleting…' : 'Delete empty notebook'}
              </button>
            )}

            <button
              className="btn btn-secondary"
              onClick={() => {
                build.reset();
                onClose();
              }}
            >
              Done
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- select phase (default) -----------------------------------------------
  return (
    <div className="stack">
      <div className="row-between">
        <h2 style={{ margin: 0 }}>Create notebook from results</h2>
        <button className="btn btn-secondary btn-sm" onClick={onClose}>
          Cancel
        </button>
      </div>

      <ErrorMessage error={build.error} />

      <div className="card">
        <div className="field">
          <label>Notebook name</label>
          <input
            className="input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={255}
            required
          />
        </div>
        <div className="field">
          <label>Description (optional)</label>
          <textarea
            className="textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={2000}
          />
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label>Tags (comma-separated)</label>
          <input className="input" value={tags} onChange={(e) => setTags(e.target.value)} />
        </div>
      </div>

      <div className="row-between">
        <h3 style={{ margin: 0, fontSize: '1rem' }}>
          Sources ({selected.size} of {displayArticles.length} selected)
        </h3>
        <button className="btn btn-secondary btn-sm" onClick={toggleAll}>
          {allSelected ? 'Select none' : 'Select all'}
        </button>
      </div>

      <div>
        {displayArticles.map((a) => (
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
        <button
          className="btn"
          onClick={handleCreate}
          disabled={!name.trim() || selected.size === 0}
        >
          Create notebook
        </button>
        <button className="btn btn-secondary" onClick={onClose}>
          Cancel
        </button>
      </div>
    </div>
  );
}
