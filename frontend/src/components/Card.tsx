export function Card({
  title,
  action,
  children,
  style,
  className,
}: {
  title?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
}) {
  return (
    <div className={`card ${className ?? ""}`} style={style}>
      {(title || action) && (
        <div className="card-header">
          {title && <h3>{title}</h3>}
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

export function StatTile({ label, value, detail }: { label: string; value: React.ReactNode; detail?: string }) {
  return (
    <div className="stat-tile">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {detail && <div className="stat-detail">{detail}</div>}
    </div>
  );
}
