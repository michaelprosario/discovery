import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useGenerateBlogPost } from '../hooks/queries';
import { ErrorMessage } from '../components/ErrorMessage';

const TONES = ['informative', 'casual', 'formal', 'academic', 'conversational'];

export function NewBlogPostPage() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const generate = useGenerateBlogPost(id);

  const [title, setTitle] = useState('');
  const [prompt, setPrompt] = useState('');
  const [tone, setTone] = useState('informative');
  const [targetWordCount, setTargetWordCount] = useState(550);
  const [includeReferences, setIncludeReferences] = useState(true);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const output = await generate.mutateAsync({
      title: title.trim(),
      prompt: prompt.trim() || undefined,
      tone,
      target_word_count: targetWordCount,
      include_references: includeReferences,
    });
    navigate(`/notebooks/${id}/outputs/${output.id}`);
  }

  return (
    <div className="stack" style={{ maxWidth: 640 }}>
      <Link to={`/notebooks/${id}`} className="text-sm muted">
        ← Back to notebook
      </Link>
      <h1>Generate blog post</h1>
      <p className="muted">
        Synthesizes a blog post from this notebook's sources. Make sure your sources are extracted.
      </p>

      <div className="card">
        <ErrorMessage error={generate.error} />
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Title</label>
            <input
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={500}
            />
          </div>
          <div className="field">
            <label>Custom prompt (optional)</label>
            <textarea
              className="textarea"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              maxLength={5000}
              placeholder="Any specific angle, audience, or instructions…"
            />
          </div>
          <div className="row" style={{ alignItems: 'flex-end' }}>
            <div className="field" style={{ flex: 1 }}>
              <label>Tone</label>
              <select className="select" value={tone} onChange={(e) => setTone(e.target.value)}>
                {TONES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>Target word count</label>
              <input
                className="input"
                type="number"
                min={100}
                max={2000}
                value={targetWordCount}
                onChange={(e) => setTargetWordCount(Number(e.target.value))}
              />
            </div>
          </div>
          <div className="field">
            <label className="row" style={{ fontWeight: 400 }}>
              <input
                type="checkbox"
                checked={includeReferences}
                onChange={(e) => setIncludeReferences(e.target.checked)}
              />
              Include reference links at the bottom
            </label>
          </div>
          <button className="btn" type="submit" disabled={!title.trim() || generate.isPending}>
            {generate.isPending ? 'Generating… (this may take a moment)' : 'Generate blog post'}
          </button>
        </form>
      </div>
    </div>
  );
}
