import { DOMAIN_LABEL, DOMAIN_VAR } from "../lib/domain";
import type { Domain } from "../types";

type BadgeTone = "ok" | "warn" | "danger" | "muted" | "gold";

const STATUS_TONE: Record<string, BadgeTone> = {
  SUPPORTED: "ok",
  COMPLETED: "ok",
  APPROVED: "ok",
  ok: "ok",
  configured: "ok",
  NOT_SUPPORTED: "danger",
  FAILED: "danger",
  REJECTED: "danger",
  INCONCLUSIVE: "warn",
  PENDING: "warn",
  RUNNING: "warn",
  degraded: "warn",
};

/** Renders a status/enum value with a consistent color mapping across the
 * app, so "SUPPORTED" always reads green and "NOT_SUPPORTED" always reads
 * red wherever it appears (dashboard, experiment approval, quantum lab). */
export function StatusBadge({ value }: { value: string }) {
  const tone = STATUS_TONE[value] ?? "muted";
  return (
    <span className={`badge ${tone}`}>
      <span className="badge-dot" />
      {value.replace(/_/g, " ")}
    </span>
  );
}

export function Badge({ tone = "muted", children }: { tone?: BadgeTone; children: React.ReactNode }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

/** A colored dot + label tag for a research domain, using a fixed
 * per-domain hue (Section taxonomy) so AI/Cybersecurity/Quantum/PQC read as
 * distinct categories at a glance across every list in the app. */
export function DomainTag({ domain }: { domain: Domain }) {
  return (
    <span className="domain-tag" style={{ color: DOMAIN_VAR[domain] }}>
      <span className="badge-dot" />
      {DOMAIN_LABEL[domain]}
    </span>
  );
}
