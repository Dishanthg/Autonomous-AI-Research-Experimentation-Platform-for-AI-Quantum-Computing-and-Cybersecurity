import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { Card } from "../components/Card";
import { Badge } from "../components/Badge";
import { EmptyState, SkeletonRows } from "../components/EmptyState";
import { IconClipboard } from "../components/icons";

interface AuditLogRow {
  id: string;
  actor_user_id: string | null;
  actor_type: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  created_at: string;
}

/** Section 46 page 20 / Section 90. Read-only, ADMIN-only (matches the
 * backend's require_admin dependency on GET /api/v1/audit) - every
 * approval-gate decision and state transition is visible here. */
export default function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLogRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<AuditLogRow[]>("/audit?limit=200")
      .then(setLogs)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load audit log."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Audit Log</h2>
          <div className="subtitle">
            Every human approval-gate decision, config change, and sandbox execution — admin-only, read-only.
          </div>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          {error.toLowerCase().includes("not permitted") && " — this view requires the ADMIN role."}
        </div>
      )}

      <Card className="card-flush">
        {loading ? (
          <div style={{ padding: 20 }}><SkeletonRows rows={5} height={20} /></div>
        ) : logs.length === 0 && !error ? (
          <EmptyState icon={<IconClipboard size={28} />} title="No audit entries yet" description="Actions across the platform will appear here as they happen." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Time (UTC)</th><th>Actor</th><th>Action</th><th>Resource</th></tr></thead>
              <tbody>
                {logs.map((row) => (
                  <tr key={row.id}>
                    <td className="mono tiny faint">{new Date(row.created_at).toLocaleString()}</td>
                    <td><Badge tone={row.actor_type === "human" ? "ok" : "muted"}>{row.actor_type}</Badge></td>
                    <td className="mono tiny">{row.action}</td>
                    <td className="tiny muted">
                      {row.resource_type}{row.resource_id ? ` · ${row.resource_id.slice(0, 8)}` : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
