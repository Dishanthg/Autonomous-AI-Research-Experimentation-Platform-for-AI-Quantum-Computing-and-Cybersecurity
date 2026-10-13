import type { ReactNode } from "react";
import { IconInbox } from "./icons";

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      {icon ?? <IconInbox size={30} />}
      <div className="empty-title">{title}</div>
      {description && <div className="empty-desc">{description}</div>}
      {action && <div className="empty-action">{action}</div>}
    </div>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--text-dim)", fontSize: 13 }}>
      <span className="spinner" />
      {label ?? "Loading…"}
    </div>
  );
}

export function SkeletonRows({ rows = 3, height = 14 }: { rows?: number; height?: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skeleton" style={{ height, width: `${100 - i * 12}%` }} />
      ))}
    </div>
  );
}
