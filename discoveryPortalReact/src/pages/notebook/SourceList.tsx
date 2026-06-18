import { Link } from 'react-router-dom';
import { useDeleteSource, useExtractContent, useSources } from '../../hooks/queries';
import type { Source } from '../../api/types';
import { Spinner } from '../../components/Spinner';
import { ErrorMessage } from '../../components/ErrorMessage';

function sourceMeta(s: Source): string {
  if (s.source_type === 'url') return s.url ?? 'URL';
  if (s.source_type === 'file') return `${s.file_type?.toUpperCase() ?? 'FILE'}`;
  return 'Text';
}

function SourceRow({ source, notebookId }: { source: Source; notebookId: string }) {
  const extract = useExtractContent(notebookId);
  const remove = useDeleteSource(notebookId);
  const hasText = source.extracted_text.trim().length > 0;

  return (
    <div className="card">
      <div className="row-between">
        <div style={{ minWidth: 0 }}>
          <h3 style={{ fontSize: '1rem', marginBottom: 2 }}>
            <Link to={`/notebooks/${notebookId}/sources/${source.id}`}>{source.name}</Link>
          </h3>
          <p className="text-sm muted" style={{ margin: 0 }}>
            <span className="tag">{source.source_type}</span>
            {sourceMeta(source)} ·{' '}
            {hasText ? `${source.extracted_text.length.toLocaleString()} chars` : 'not extracted'}
          </p>
        </div>
        <div className="row">
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => extract.mutate({ id: source.id, force: true })}
            disabled={extract.isPending}
            title="Re-extract text content from the source"
          >
            {extract.isPending ? 'Extracting…' : 'Extract'}
          </button>
          <button
            className="btn btn-danger btn-sm"
            onClick={() => {
              if (confirm(`Delete source "${source.name}"?`)) remove.mutate(source.id);
            }}
            disabled={remove.isPending}
          >
            Delete
          </button>
        </div>
      </div>
      <ErrorMessage error={extract.error || remove.error} />
    </div>
  );
}

export function SourceList({ notebookId }: { notebookId: string }) {
  const { data, isLoading, error } = useSources(notebookId);

  if (isLoading) return <Spinner label="Loading sources…" />;
  if (error) return <ErrorMessage error={error} />;
  if (!data || data.sources.length === 0) {
    return (
      <div className="card">
        <p className="muted">No sources yet. Add a file, URL, or text snippet above.</p>
      </div>
    );
  }

  return (
    <div className="stack">
      {data.sources.map((s) => (
        <SourceRow key={s.id} source={s} notebookId={notebookId} />
      ))}
    </div>
  );
}
