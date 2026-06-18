import { useState } from 'react';
import { useUpdateNotebook } from '../../hooks/queries';
import type { Notebook } from '../../api/types';
import { ErrorMessage } from '../../components/ErrorMessage';

/** Edit description and tags (UpdateNotebookCommand). */
export function NotebookSettings({ notebook }: { notebook: Notebook }) {
  const update = useUpdateNotebook(notebook.id);
  const [open, setOpen] = useState(false);
  const [description, setDescription] = useState(notebook.description ?? '');
  const [tags, setTags] = useState(notebook.tags.join(', '));
  const [saved, setSaved] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaved(false);
    await update.mutateAsync({
      description: description.trim(),
      tags: tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
    });
    setSaved(true);
  }

  if (!open) {
    return (
      <div className="card row-between">
        <div style={{ minWidth: 0 }}>
          {notebook.description ? (
            <p style={{ margin: 0 }}>{notebook.description}</p>
          ) : (
            <p className="muted" style={{ margin: 0 }}>
              No description.
            </p>
          )}
          <div style={{ marginTop: 6 }}>
            {notebook.tags.map((t) => (
              <span key={t} className="tag">
                {t}
              </span>
            ))}
          </div>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={() => setOpen(true)}>
          Edit details
        </button>
      </div>
    );
  }

  return (
    <div className="card">
      <ErrorMessage error={update.error} />
      {saved && <div className="alert alert-success">Saved.</div>}
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>Description</label>
          <textarea
            className="textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={2000}
          />
        </div>
        <div className="field">
          <label>Tags (comma-separated)</label>
          <input className="input" value={tags} onChange={(e) => setTags(e.target.value)} />
        </div>
        <div className="row">
          <button className="btn" type="submit" disabled={update.isPending}>
            {update.isPending ? 'Saving…' : 'Save'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={() => setOpen(false)}>
            Close
          </button>
        </div>
      </form>
    </div>
  );
}
