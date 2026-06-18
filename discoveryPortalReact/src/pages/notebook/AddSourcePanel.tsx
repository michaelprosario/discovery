import { useState } from 'react';
import {
  useImportFileSource,
  useImportTextSource,
  useImportUrlSource,
} from '../../hooks/queries';
import { ErrorMessage } from '../../components/ErrorMessage';
import { fileToBase64, fileTypeFromName } from '../../lib/files';

type Tab = 'file' | 'url' | 'text';

export function AddSourcePanel({ notebookId }: { notebookId: string }) {
  const [tab, setTab] = useState<Tab>('file');
  const [open, setOpen] = useState(false);

  const importFile = useImportFileSource(notebookId);
  const importUrl = useImportUrlSource(notebookId);
  const importText = useImportTextSource(notebookId);

  // file
  const [file, setFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState('');
  // url
  const [url, setUrl] = useState('');
  const [urlTitle, setUrlTitle] = useState('');
  // text
  const [textTitle, setTextTitle] = useState('');
  const [textContent, setTextContent] = useState('');

  const [localError, setLocalError] = useState<string | null>(null);

  function reset() {
    setFile(null);
    setFileName('');
    setUrl('');
    setUrlTitle('');
    setTextTitle('');
    setTextContent('');
    setLocalError(null);
  }

  async function submitFile(e: React.FormEvent) {
    e.preventDefault();
    setLocalError(null);
    if (!file) return;
    const fileType = fileTypeFromName(file.name);
    if (!fileType) {
      setLocalError('Unsupported file type. Use pdf, docx, doc, txt, or md.');
      return;
    }
    const file_content = await fileToBase64(file);
    await importFile.mutateAsync({
      notebook_id: notebookId,
      name: (fileName || file.name).trim(),
      file_content,
      file_type: fileType,
    });
    reset();
    setOpen(false);
  }

  async function submitUrl(e: React.FormEvent) {
    e.preventDefault();
    await importUrl.mutateAsync({
      notebook_id: notebookId,
      url: url.trim(),
      title: urlTitle.trim() || undefined,
    });
    reset();
    setOpen(false);
  }

  async function submitText(e: React.FormEvent) {
    e.preventDefault();
    await importText.mutateAsync({
      notebook_id: notebookId,
      title: textTitle.trim(),
      content: textContent.trim(),
    });
    reset();
    setOpen(false);
  }

  if (!open) {
    return (
      <button className="btn" onClick={() => setOpen(true)}>
        + Add source
      </button>
    );
  }

  const tabBtn = (t: Tab, label: string) => (
    <button
      type="button"
      className={`btn btn-sm ${tab === t ? '' : 'btn-secondary'}`}
      onClick={() => {
        setTab(t);
        setLocalError(null);
      }}
    >
      {label}
    </button>
  );

  return (
    <div className="card stack">
      <div className="row-between">
        <h3>Add source</h3>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => {
            reset();
            setOpen(false);
          }}
        >
          Cancel
        </button>
      </div>
      <div className="row">
        {tabBtn('file', 'File')}
        {tabBtn('url', 'URL')}
        {tabBtn('text', 'Text')}
      </div>

      <ErrorMessage error={localError || importFile.error || importUrl.error || importText.error} />

      {tab === 'file' && (
        <form onSubmit={submitFile}>
          <div className="field">
            <label>File (pdf, docx, doc, txt, md)</label>
            <input
              className="input"
              type="file"
              accept=".pdf,.docx,.doc,.txt,.md"
              onChange={(e) => {
                const f = e.target.files?.[0] ?? null;
                setFile(f);
                if (f && !fileName) setFileName(f.name);
              }}
            />
          </div>
          <div className="field">
            <label>Display name</label>
            <input
              className="input"
              value={fileName}
              onChange={(e) => setFileName(e.target.value)}
              placeholder="Defaults to file name"
            />
          </div>
          <button className="btn" type="submit" disabled={!file || importFile.isPending}>
            {importFile.isPending ? 'Uploading…' : 'Import file'}
          </button>
        </form>
      )}

      {tab === 'url' && (
        <form onSubmit={submitUrl}>
          <div className="field">
            <label>URL</label>
            <input
              className="input"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/article"
              required
            />
          </div>
          <div className="field">
            <label>Title (optional)</label>
            <input
              className="input"
              value={urlTitle}
              onChange={(e) => setUrlTitle(e.target.value)}
              placeholder="Extracted from page if blank"
            />
          </div>
          <button className="btn" type="submit" disabled={!url.trim() || importUrl.isPending}>
            {importUrl.isPending ? 'Fetching…' : 'Import URL'}
          </button>
        </form>
      )}

      {tab === 'text' && (
        <form onSubmit={submitText}>
          <div className="field">
            <label>Title</label>
            <input
              className="input"
              value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label>Content</label>
            <textarea
              className="textarea"
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              required
              style={{ minHeight: 160 }}
            />
          </div>
          <button
            className="btn"
            type="submit"
            disabled={!textTitle.trim() || !textContent.trim() || importText.isPending}
          >
            {importText.isPending ? 'Saving…' : 'Add text'}
          </button>
        </form>
      )}
    </div>
  );
}
