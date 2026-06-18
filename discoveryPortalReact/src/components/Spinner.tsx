export function Spinner({ label }: { label?: string }) {
  return (
    <div className="row" style={{ padding: '2rem 0', justifyContent: 'center' }}>
      <div className="spinner" />
      {label && <span className="muted">{label}</span>}
    </div>
  );
}
