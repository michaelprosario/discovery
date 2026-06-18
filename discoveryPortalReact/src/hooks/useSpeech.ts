import { useCallback, useEffect, useRef, useState } from 'react';

export type SpeechStatus = 'idle' | 'speaking' | 'paused';

/**
 * Split text into short, sentence-aligned chunks. Browsers (notably Chrome)
 * truncate a single long utterance after ~15s, so we queue many small ones.
 */
function chunkText(text: string): string[] {
  const sentences = text.match(/[^.!?\n]+[.!?]*\s*/g) ?? [text];
  const chunks: string[] = [];
  let current = '';
  for (const sentence of sentences) {
    if (current && (current + sentence).length > 220) {
      chunks.push(current.trim());
      current = '';
    }
    current += sentence;
  }
  if (current.trim()) chunks.push(current.trim());
  return chunks.filter(Boolean);
}

/**
 * Wraps the Web Speech `speechSynthesis` API with start / pause / resume /
 * restart / stop and a reactive status. Each playback gets a generation id so
 * the async end/error callbacks from a cancelled run can't clobber the status
 * of a newly started one.
 */
export function useSpeech() {
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window;
  const [status, setStatus] = useState<SpeechStatus>('idle');
  const textRef = useRef('');
  const genRef = useRef(0);

  const start = useCallback(
    (text: string) => {
      if (!supported) return;
      const synth = window.speechSynthesis;
      const gen = ++genRef.current;
      synth.cancel(); // clears any queued/old utterances (fires their handlers with a stale gen)

      textRef.current = text;
      const chunks = chunkText(text);
      if (chunks.length === 0) return;

      chunks.forEach((chunk, i) => {
        const utterance = new SpeechSynthesisUtterance(chunk);
        utterance.lang = 'en-US';
        utterance.rate = 1;
        if (i === chunks.length - 1) {
          utterance.onend = () => {
            if (genRef.current === gen) setStatus('idle');
          };
        }
        utterance.onerror = () => {
          if (genRef.current === gen) setStatus('idle');
        };
        synth.speak(utterance);
      });
      setStatus('speaking');
    },
    [supported],
  );

  const pause = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.pause();
    setStatus('paused');
  }, [supported]);

  const resume = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.resume();
    setStatus('speaking');
  }, [supported]);

  const restart = useCallback(() => {
    if (textRef.current) start(textRef.current);
  }, [start]);

  const stop = useCallback(() => {
    if (!supported) return;
    genRef.current++;
    window.speechSynthesis.cancel();
    setStatus('idle');
  }, [supported]);

  // Stop any in-flight speech if the component unmounts (e.g. navigating away).
  useEffect(() => {
    return () => {
      if (supported) window.speechSynthesis.cancel();
    };
  }, [supported]);

  return { supported, status, start, pause, resume, restart, stop };
}
