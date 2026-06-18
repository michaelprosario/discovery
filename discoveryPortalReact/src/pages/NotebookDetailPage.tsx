import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useNotebook } from '../hooks/queries';
import { Spinner } from '../components/Spinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { NotebookHeader } from './notebook/NotebookHeader';
import { NotebookSettings } from './notebook/NotebookSettings';
import { IndexPanel } from './notebook/IndexPanel';
import { AddSourcePanel } from './notebook/AddSourcePanel';
import { SourceList } from './notebook/SourceList';
import { OutputsSection } from './notebook/OutputsSection';

type Tab = 'sources' | 'outputs';

export function NotebookDetailPage() {
  const { id = '' } = useParams();
  const { data: notebook, isLoading, error } = useNotebook(id);
  const [tab, setTab] = useState<Tab>('sources');

  if (isLoading) return <Spinner label="Loading notebook…" />;
  if (error) return <ErrorMessage error={error} />;
  if (!notebook) return <ErrorMessage error="Notebook not found." />;

  const tabBtn = (t: Tab, label: string, count: number) => (
    <button
      type="button"
      className={`btn btn-sm ${tab === t ? '' : 'btn-secondary'}`}
      onClick={() => setTab(t)}
    >
      {label} ({count})
    </button>
  );

  return (
    <div className="stack">
      <Link to="/notebooks" className="text-sm muted">
        ← All notebooks
      </Link>

      <NotebookHeader notebook={notebook} />
      <NotebookSettings notebook={notebook} />

      <div className="row" style={{ flexWrap: 'wrap' }}>
        <Link to={`/notebooks/${id}/chat`} className="btn">
          💬 Ask questions
        </Link>
        <Link to={`/notebooks/${id}/new-blog-post`} className="btn">
          ✍️ Generate blog post
        </Link>
      </div>

      <IndexPanel notebookId={id} />

      <div className="row">
        {tabBtn('sources', 'Sources', notebook.source_count)}
        {tabBtn('outputs', 'Outputs', notebook.output_count)}
      </div>

      {tab === 'sources' ? (
        <div className="stack">
          <AddSourcePanel notebookId={id} />
          <SourceList notebookId={id} />
        </div>
      ) : (
        <OutputsSection notebookId={id} />
      )}
    </div>
  );
}
