import { Link } from 'react-router-dom';
import { useDeleteOutput, useOutputs } from '../../hooks/queries';
import { Spinner } from '../../components/Spinner';
import { ErrorMessage } from '../../components/ErrorMessage';

export function OutputsSection({ notebookId }: { notebookId: string }) {
  const { data, isLoading, error } = useOutputs(notebookId);
  const del = useDeleteOutput(notebookId);

  if (isLoading) return <Spinner label="Loading outputs…" />;
  if (error) return <ErrorMessage error={error} />;
  if (!data || data.outputs.length === 0) {
    return (
      <div className="card">
        <p className="muted">No generated outputs yet. Generate a blog post to get started.</p>
      </div>
    );
  }

  return (
    <div className="stack">
      <ErrorMessage error={del.error} />
      {data.outputs.map((o) => (
        <div key={o.id} className="card row-between">
          <div style={{ minWidth: 0 }}>
            <h3 style={{ fontSize: '1rem', marginBottom: 2 }}>
              <Link to={`/notebooks/${notebookId}/outputs/${o.id}`}>{o.title}</Link>
            </h3>
            <p className="text-sm muted" style={{ margin: 0 }}>
              <span className="tag">{o.output_type}</span>
              {o.status} · {o.word_count.toLocaleString()} words
            </p>
          </div>
          <button
            className="btn btn-danger btn-sm"
            onClick={() => {
              if (confirm(`Delete output "${o.title}"?`)) del.mutate(o.id);
            }}
            disabled={del.isPending}
          >
            Delete
          </button>
        </div>
      ))}
    </div>
  );
}
