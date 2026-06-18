import { Link, useParams } from 'react-router-dom';
import { useOutput } from '../hooks/queries';
import { Spinner } from '../components/Spinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { Markdown } from '../components/Markdown';

export function ViewOutputPage() {
  const { id = '', outputId = '' } = useParams();
  const { data: output, isLoading, error } = useOutput(outputId);

  if (isLoading) return <Spinner label="Loading output…" />;
  if (error) return <ErrorMessage error={error} />;
  if (!output) return <ErrorMessage error="Output not found." />;

  return (
    <div className="stack" style={{ maxWidth: 760 }}>
      <Link to={`/notebooks/${id}`} className="text-sm muted">
        ← Back to notebook
      </Link>
      <div>
        <h1 style={{ marginBottom: 4 }}>{output.title}</h1>
        <p className="text-sm muted" style={{ margin: 0 }}>
          <span className="tag">{output.output_type}</span>
          {output.status} · {output.word_count.toLocaleString()} words
        </p>
      </div>

      <div className="card">
        <Markdown>{output.content || '_No content._'}</Markdown>
      </div>

      {output.source_references.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: '1rem' }}>Sources used</h3>
          <ul className="text-sm">
            {output.source_references.map((ref, i) => (
              <li key={i}>{ref}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
