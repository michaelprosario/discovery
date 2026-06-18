import { useIngestNotebook, useVectorCount } from '../../hooks/queries';
import { ErrorMessage } from '../../components/ErrorMessage';

/**
 * Vector indexing ("IndexContent"). Q&A and article-grounded search require
 * the notebook's sources to be chunked and embedded into the vector DB first.
 */
export function IndexPanel({ notebookId }: { notebookId: string }) {
  const count = useVectorCount(notebookId);
  const ingest = useIngestNotebook(notebookId);

  return (
    <div className="card stack">
      <div className="row-between">
        <div>
          <h3 style={{ fontSize: '1rem' }}>Search index</h3>
          <p className="text-sm muted" style={{ margin: 0 }}>
            {count.isLoading
              ? 'Checking index…'
              : count.data
                ? `${count.data.vector_count.toLocaleString()} chunk(s) indexed`
                : 'Not indexed yet'}
          </p>
        </div>
        <button
          className="btn btn-secondary"
          onClick={() => ingest.mutate(true)}
          disabled={ingest.isPending}
        >
          {ingest.isPending ? 'Indexing…' : 'Index content'}
        </button>
      </div>
      <ErrorMessage error={ingest.error} />
      {ingest.isSuccess && ingest.data && (
        <div className="alert alert-success">{ingest.data.message}</div>
      )}
      <p className="text-sm muted" style={{ margin: 0 }}>
        Index your sources to enable Q&amp;A and grounded search. Re-run after adding sources.
      </p>
    </div>
  );
}
