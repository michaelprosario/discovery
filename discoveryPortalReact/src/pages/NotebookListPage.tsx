import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useNotebooks } from '../hooks/queries';
import type { ListNotebooksParams } from '../api/services';
import { Spinner } from '../components/Spinner';
import { ErrorMessage } from '../components/ErrorMessage';

export function NotebookListPage() {
  const [sort, setSort] = useState<ListNotebooksParams>({
    sortBy: 'updated_at',
    sortOrder: 'desc',
  });
  const { data, isLoading, error } = useNotebooks(sort);

  return (
    <div className="stack">
      <div className="row-between">
        <div>
          <h1>Notebooks</h1>
          <p className="muted">{data ? `${data.total} notebook(s)` : 'Your research workspaces'}</p>
        </div>
        <Link to="/notebooks/new" className="btn">
          + New notebook
        </Link>
      </div>

      <div className="row">
        <select
          className="select"
          style={{ width: 'auto' }}
          value={`${sort.sortBy}:${sort.sortOrder}`}
          onChange={(e) => {
            const [sortBy, sortOrder] = e.target.value.split(':') as [
              ListNotebooksParams['sortBy'],
              ListNotebooksParams['sortOrder'],
            ];
            setSort({ sortBy, sortOrder });
          }}
        >
          <option value="updated_at:desc">Recently updated</option>
          <option value="created_at:desc">Newest</option>
          <option value="created_at:asc">Oldest</option>
          <option value="name:asc">Name (A–Z)</option>
          <option value="name:desc">Name (Z–A)</option>
        </select>
      </div>

      <ErrorMessage error={error} />
      {isLoading ? (
        <Spinner label="Loading notebooks…" />
      ) : !data || data.notebooks.length === 0 ? (
        <div className="card">
          <p className="muted">No notebooks yet. Create your first one to get started.</p>
        </div>
      ) : (
        <div className="grid">
          {data.notebooks.map((nb) => (
            <Link
              key={nb.id}
              to={`/notebooks/${nb.id}`}
              className="card"
              style={{ color: 'inherit' }}
            >
              <h3>{nb.name}</h3>
              {nb.description && <p className="muted text-sm">{nb.description}</p>}
              <div style={{ margin: '0.5rem 0' }}>
                {nb.tags.map((t) => (
                  <span key={t} className="tag">
                    {t}
                  </span>
                ))}
              </div>
              <p className="text-sm muted">
                {nb.source_count} source(s) · {nb.output_count} output(s)
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
