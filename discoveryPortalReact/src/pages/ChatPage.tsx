import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { qaApi } from '../api/services';
import type { QaResponse } from '../api/types';
import { ErrorMessage } from '../components/ErrorMessage';
import { Markdown } from '../components/Markdown';
import { CopyButton } from '../components/CopyButton';
import styles from './ChatPage.module.css';


interface Turn {
  question: string;
  response?: QaResponse;
}

export function ChatPage() {
  const { id = '' } = useParams();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [question, setQuestion] = useState('');

  const ask = useMutation({
    mutationFn: (q: string) => qaApi.ask(id, { question: q, max_sources: 5 }),
    onSuccess: (response, q) => {
      setTurns((prev) =>
        prev.map((t) => (t.question === q && !t.response ? { ...t, response } : t)),
      );
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || ask.isPending) return;
    setTurns((prev) => [...prev, { question: q }]);
    setQuestion('');
    ask.mutate(q);
  }

  return (
    <div className="stack">
      <Link to={`/notebooks/${id}`} className="text-sm muted">
        ← Back to notebook
      </Link>
      <div>
        <h1 style={{ marginBottom: 4 }}>Ask this notebook</h1>
        <p className="muted">
          Answers are grounded in your indexed sources, with citations. Index the notebook first if
          you get no results.
        </p>
      </div>

      <ErrorMessage error={ask.error} />

      <div className={styles.thread}>
        {turns.map((turn, i) => (
          <div key={i} style={{ display: 'contents' }}>
            <div className={styles.question}>{turn.question}</div>
            <div className={`card ${styles.answer}`}>
              {turn.response ? (
                <>
                  <Markdown>{turn.response.answer}</Markdown>
                  <div style={{ marginTop: '0.5rem', display: 'flex', justifyContent: 'flex-end' }}>
                    <CopyButton content={turn.response.answer} />
                  </div>
                  {turn.response.sources.length > 0 && (
                    <div className={styles.sources}>
                      <p className="text-sm muted" style={{ marginTop: 0 }}>
                        Sources
                      </p>
                      {turn.response.sources.map((s, j) => (
                        <div key={j} className={styles.citation}>
                          <strong>
                            [{j + 1}] {s.source_name || s.source_id || 'Unknown source'}
                          </strong>
                          {typeof s.relevance_score === 'number' && (
                            <span className="muted"> · relevance {s.relevance_score.toFixed(2)}</span>
                          )}
                          <div className="muted" style={{ marginTop: 4 }}>
                            {s.text.length > 280 ? `${s.text.slice(0, 280)}…` : s.text}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <span className="muted">Thinking…</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className={styles.composer}>
        <input
          className="input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your sources…"
        />
        <button className="btn" type="submit" disabled={!question.trim() || ask.isPending}>
          {ask.isPending ? 'Asking…' : 'Ask'}
        </button>
      </form>
    </div>
  );
}
