import ReactMarkdown from 'react-markdown';

/** Renders markdown content (outputs, Q&A answers) inside a styled block. */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="markdown">
      <ReactMarkdown>{children}</ReactMarkdown>
    </div>
  );
}
