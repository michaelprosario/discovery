import { useState } from 'react';

interface CopyButtonProps {
  content: string;
  className?: string;
}

export function CopyButton({ content, className = '' }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <button
      className={`btn btn-secondary btn-sm ${className}`}
      onClick={handleCopy}
      style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
      title="Copy to clipboard"
    >
      {copied ? '✅ Copied!' : '📋 Copy text'}
    </button>
  );
}
