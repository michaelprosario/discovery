import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { articleApi } from '../api/services';
import { ErrorMessage } from '../components/ErrorMessage';
import { CreateNotebookFromResults } from './articleSearch/CreateNotebookFromResults';

export function ArticleSearchPage() {
  const [question, setQuestion] = useState('');
  const [maxResults, setMaxResults] = useState(10);
  // The question that produced the current results (for prefilling the notebook).
  const [submittedQuestion, setSubmittedQuestion] = useState('');
  const [building, setBuilding] = useState(false);

  const search = useMutation({
    mutationFn: () => articleApi.search({ question: question.trim(), max_results: maxResults }),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setBuilding(false);
    setSubmittedQuestion(question.trim());
    search.mutate();
  }

  const articles = search.data?.robust_articles ?? [];

  return (
    <div className="stack" style={{ maxWidth: 720 }}>
      <div>
        <h1>Article search</h1>
        <p className="muted">
          Find relevant articles on the web for a question or topic. Useful for discovering sources
          to import into a notebook.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="card">
        <div className="field">
          <label>Question or topic</label>
          <input
            className="input"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. How does retrieval-augmented generation work?"
            required
          />
        </div>
        <div className="row" style={{ alignItems: 'flex-end' }}>
          <div className="field" style={{ width: 160, marginBottom: 0 }}>
            <label>Max results</label>
            <input
              className="input"
              type="number"
              min={1}
              max={20}
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
            />
          </div>
          <button className="btn" type="submit" disabled={!question.trim() || search.isPending}>
            {search.isPending ? 'Searching…' : 'Search'}
          </button>
        </div>
      </form>

      <ErrorMessage error={search.error} />

      {building ? (
        <CreateNotebookFromResults
          articles={articles}
          question={submittedQuestion}
          onClose={() => setBuilding(false)}
        />
      ) : (
        search.isSuccess &&
        (articles.length === 0 ? (
          <div className="card">
            <p className="muted">No articles found.</p>
          </div>
        ) : (
          <div className="stack">
            <div className="row-between">
              <h2 style={{ margin: 0, fontSize: '1.1rem' }}>{articles.length} result(s)</h2>
              <button className="btn" onClick={() => setBuilding(true)}>
                + Create notebook
              </button>
            </div>
            {articles.map((a, i) => (
              <div key={i} className="card">
                <h3 style={{ fontSize: '1rem', marginBottom: 2 }}>
                  <a href={a.link} target="_blank" rel="noreferrer">
                    {a.title}
                  </a>
                </h3>
                <p className="text-sm muted" style={{ margin: 0, wordBreak: 'break-all' }}>
                  {a.link}
                </p>
              </div>
            ))}
          </div>
        ))
      )}
    </div>
  );
}
