import type { AddedArticle, FailedArticle } from '../hooks/articleIngest';
import styles from './IngestReport.module.css';

/**
 * Shared "added / could-not-be-ingested" report, rendered on the summary screen
 * of both the create-notebook-from-search and add-sources-to-notebook flows.
 */
export function IngestReport({
  added,
  failed,
}: {
  added: AddedArticle[];
  failed: FailedArticle[];
}) {
  return (
    <>
      {added.length > 0 && (
        <div>
          <h3 style={{ fontSize: '1rem' }}>✅ Added with no issues</h3>
          {added.map((a) => (
            <div key={a.link} className={`${styles.reportItem} ${styles.added}`}>
              <div style={{ fontWeight: 600 }}>{a.title}</div>
              <a href={a.link} target="_blank" rel="noreferrer" className={styles.articleLink}>
                {a.link}
              </a>
            </div>
          ))}
        </div>
      )}

      {failed.length > 0 && (
        <div>
          <h3 style={{ fontSize: '1rem' }}>⚠️ Could not be ingested</h3>
          {failed.map((f) => (
            <div key={f.link} className={`${styles.reportItem} ${styles.failed}`}>
              <div style={{ fontWeight: 600 }}>{f.title}</div>
              <a href={f.link} target="_blank" rel="noreferrer" className={styles.articleLink}>
                {f.link}
              </a>
              <div className={styles.reason}>Reason: {f.reason}</div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
