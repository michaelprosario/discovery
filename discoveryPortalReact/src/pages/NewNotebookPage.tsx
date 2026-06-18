import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useCreateNotebook } from '../hooks/queries';
import { ErrorMessage } from '../components/ErrorMessage';

export function NewNotebookPage() {
  const navigate = useNavigate();
  const create = useCreateNotebook();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const notebook = await create.mutateAsync({
      name: name.trim(),
      description: description.trim() || undefined,
      tags: tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
    });
    navigate(`/notebooks/${notebook.id}`);
  }

  return (
    <div className="stack" style={{ maxWidth: 560 }}>
      <div>
        <Link to="/notebooks" className="text-sm muted">
          ← Back to notebooks
        </Link>
        <h1>New notebook</h1>
      </div>
      <div className="card">
        <ErrorMessage error={create.error} />
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="name">Name</label>
            <input
              id="name"
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              maxLength={255}
            />
          </div>
          <div className="field">
            <label htmlFor="description">Description (optional)</label>
            <textarea
              id="description"
              className="textarea"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={2000}
            />
          </div>
          <div className="field">
            <label htmlFor="tags">Tags (comma-separated)</label>
            <input
              id="tags"
              className="input"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="research, ai, notes"
            />
          </div>
          <div className="row">
            <button className="btn" type="submit" disabled={create.isPending || !name.trim()}>
              {create.isPending ? 'Creating…' : 'Create notebook'}
            </button>
            <Link to="/notebooks" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
