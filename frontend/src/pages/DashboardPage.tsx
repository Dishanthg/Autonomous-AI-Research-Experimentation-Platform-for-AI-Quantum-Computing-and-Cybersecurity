import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { Badge, DomainTag, StatusBadge } from "../components/Badge";
import { Card, StatTile } from "../components/Card";
import { EmptyState, SkeletonRows } from "../components/EmptyState";
import { useToast } from "../components/Toast";
import { IconArrowRight, IconFlask, IconPlus } from "../components/icons";
import type { Project, Domain, HealthStatus } from "../types";

export default function DashboardPage() {
  const toast = useToast();
  const [projects, setProjects] = useState<Project[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [domain, setDomain] = useState<Domain>("CYBERSECURITY");
  const [objectives, setObjectives] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const [p, h] = await Promise.all([
        api.get<Project[]>("/projects"),
        api.get<HealthStatus>("/health"),
      ]);
      setProjects(p);
      setHealth(h);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function createProject(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.post("/projects", { title, domain, objectives: objectives || null });
      toast.success(`Project "${title}" created.`);
      setTitle("");
      setObjectives("");
      setShowForm(false);
      await load();
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to create project.";
      setError(msg);
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  }

  const domainCounts = projects.reduce<Record<string, number>>((acc, p) => {
    acc[p.domain] = (acc[p.domain] ?? 0) + 1;
    return acc;
  }, {});
  const healthyChecks = health ? Object.values(health.checks).filter((v) => v.startsWith("ok") || v === "configured").length : 0;
  const totalChecks = health ? Object.keys(health.checks).length : 0;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Dashboard</h2>
          <div className="subtitle">An overview of every active research project and the platform's own subsystem health.</div>
        </div>
        <button onClick={() => setShowForm((s) => !s)}>
          <IconPlus size={14} />
          New project
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="grid-3" style={{ marginBottom: 4 }}>
        <StatTile label="Projects" value={loading ? "–" : projects.length} detail="across all domains" />
        <StatTile
          label="System health"
          value={health ? <StatusBadge value={health.status} /> : "–"}
          detail={health ? `${healthyChecks}/${totalChecks} subsystems ok` : undefined}
        />
        <StatTile
          label="Most active domain"
          value={
            Object.keys(domainCounts).length
              ? Object.entries(domainCounts).sort((a, b) => b[1] - a[1])[0][0]
              : "—"
          }
          detail={loading ? undefined : "by project count"}
        />
      </div>

      {health && (
        <Card title="Subsystem status" className="card-subtle">
          <div className="btn-row">
            {Object.entries(health.checks).map(([k, v]) => (
              <Badge key={k} tone={v.startsWith("ok") || v === "configured" ? "ok" : "muted"}>
                {k.replace(/_/g, " ")}: {v}
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {showForm && (
        <Card title="New research project">
          <form onSubmit={createProject}>
            <label>Title</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} required autoFocus placeholder="e.g. Graph-based intrusion detection" />
            <div className="field-row">
              <div>
                <label>Domain</label>
                <select value={domain} onChange={(e) => setDomain(e.target.value as Domain)}>
                  <option value="AI">AI</option>
                  <option value="CYBERSECURITY">Cybersecurity</option>
                  <option value="QUANTUM">Quantum</option>
                  <option value="PQC">Post-Quantum Crypto</option>
                </select>
              </div>
            </div>
            <label>Objectives <span className="hint">(optional)</span></label>
            <textarea value={objectives} onChange={(e) => setObjectives(e.target.value)} rows={3} placeholder="What is this project trying to find out?" />
            <div className="btn-row" style={{ marginTop: 14 }}>
              <button type="submit" disabled={busy}>{busy && <span className="spinner" />}Create project</button>
              <button type="button" className="ghost" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </Card>
      )}

      <Card title={`Projects (${projects.length})`}>
        {loading ? (
          <SkeletonRows rows={3} height={40} />
        ) : projects.length === 0 ? (
          <EmptyState
            icon={<IconFlask size={30} />}
            title="No research projects yet"
            description="Create your first project to start the pipeline: research question → hypothesis → experiment → statistics → conclusion."
            action={<button onClick={() => setShowForm(true)}><IconPlus size={14} />New project</button>}
          />
        ) : (
          <div className="log-list">
            {projects.map((p, i) => (
              <div className="log-entry" key={p.id}>
                <div className="log-index">{String(i + 1).padStart(2, "0")}</div>
                <div className="log-entry-main">
                  <div className="log-entry-title">
                    <Link to={`/projects/${p.id}`}>{p.title}</Link>
                  </div>
                  <div className="log-entry-meta">
                    <DomainTag domain={p.domain} />
                  </div>
                </div>
                <div className="log-entry-action">
                  <Link to={`/projects/${p.id}`} className="tiny">
                    Open <IconArrowRight size={12} style={{ verticalAlign: "-2px" }} />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
