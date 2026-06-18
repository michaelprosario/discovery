import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDeleteNotebook, useRenameNotebook } from '../../hooks/queries';
import type { Notebook } from '../../api/types';
import { ErrorMessage } from '../../components/ErrorMessage';

export function NotebookHeader({ notebook }: { notebook: Notebook }) {
  const navigate = useNavigate();
  const rename = useRenameNotebook(notebook.id);
  const del = useDeleteNotebook();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(notebook.name);

  async function submitRename(e: React.FormEvent) {
    e.preventDefault();
    if (name.trim() && name.trim() !== notebook.name) {
      await rename.mutateAsync(name.trim());
    }
    setEditing(false);
  }

  async function handleDelete() {
    if (!confirm(`Delete "${notebook.name}" and all its sources/outputs?`)) return;
    await del.mutateAsync(notebook.id);
    navigate('/notebooks');
  }

  return (
    <div className="stack">
      <div className="row-between">
        {editing ? (
          <form onSubmit={submitRename} className="row" style={{ flex: 1 }}>
            <input
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
              maxLength={255}
              style={{ maxWidth: 400 }}
            />
            <button className="btn btn-sm" type="submit" disabled={rename.isPending}>
              Save
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => {
                setName(notebook.name);
                setEditing(false);
              }}
            >
              Cancel
            </button>
          </form>
        ) : (
          <h1 style={{ margin: 0 }}>
            {notebook.name}{' '}
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => setEditing(true)}
              title="Rename notebook"
            >
              Rename
            </button>
          </h1>
        )}
        <button className="btn btn-danger btn-sm" onClick={handleDelete} disabled={del.isPending}>
          Delete
        </button>
      </div>
      <ErrorMessage error={rename.error || del.error} />
    </div>
  );
}
