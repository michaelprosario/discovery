import { useMemo } from 'react';
import { useSpeech } from '../hooks/useSpeech';
import { stripMarkdown } from '../lib/markdown';

/**
 * "Read" button + playback controls that speak the given (markdown) content
 * aloud via the browser's text-to-speech, with pause / resume / restart.
 */
export function ReadAloud({ content }: { content: string }) {
  const { supported, status, start, pause, resume, restart, stop } = useSpeech();
  const text = useMemo(() => stripMarkdown(content), [content]);

  if (!supported) {
    return (
      <span className="text-sm muted" title="Your browser does not support speech synthesis">
        🔇 Read aloud not supported
      </span>
    );
  }

  if (status === 'idle') {
    return (
      <button className="btn btn-secondary btn-sm" onClick={() => start(text)} disabled={!text}>
        🔊 Read
      </button>
    );
  }

  return (
    <div className="row">
      {status === 'speaking' ? (
        <button className="btn btn-secondary btn-sm" onClick={pause}>
          ⏸ Pause
        </button>
      ) : (
        <button className="btn btn-sm" onClick={resume}>
          ▶ Resume
        </button>
      )}
      <button className="btn btn-secondary btn-sm" onClick={restart}>
        ⏮ Restart
      </button>
      <button className="btn btn-secondary btn-sm" onClick={stop}>
        ⏹ Stop
      </button>
      <span className="text-sm muted">{status === 'paused' ? 'Paused' : 'Reading…'}</span>
    </div>
  );
}
