import { Link, useParams } from 'react-router-dom';
import { useSource } from '../hooks/queries';
import { Spinner } from '../components/Spinner';
import { ErrorMessage } from '../components/ErrorMessage';

export function SourceViewPage() {
  const { id = '', sourceId = '' } = useParams();
  const { data: source, isLoading, error } = useSource(sourceId);

  if (isLoading) return <Spinner label="Loading source…" />;
  if (error) return <ErrorMessage error={error} />;
  if (!source) return <ErrorMessage error="Source not found." />;

  return (
    <div className="stack">
      <Link to={`/notebooks/${id}`} className="text-sm muted">
        ← Back to notebook
      </Link>
      <div>
        <h1 style={{ marginBottom: 4 }}>{source.name}</h1>
        <p className="text-sm muted" style={{ margin: 0 }}>
          <span className="tag">{source.source_type}</span>
          {source.file_type && <span className="tag">{source.file_type}</span>}
          {source.url && (
            <a href={source.url} target="_blank" rel="noreferrer">
              {source.url}
            </a>
          )}
        </p>
      </div>

      <div className="card">
        <h3 style={{ fontSize: '1rem' }}>Extracted text</h3>
        {source.extracted_text.trim() ? (
          <pre
            style={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontFamily: 'inherit',
              margin: 0,
              maxHeight: 600,
              overflowY: 'auto',
            }}
          >
            {source.extracted_text}
          </pre>
        ) : (
          <p className="muted">
            No text extracted yet. Use the <strong>Extract</strong> action on the notebook page.
          </p>
        )}
      </div>
    </div>
  );
}
