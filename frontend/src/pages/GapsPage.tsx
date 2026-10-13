import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { Card } from "../components/Card";
import { Badge } from "../components/Badge";
import { EmptyState, SkeletonRows } from "../components/EmptyState";
import { useToast } from "../components/Toast";
import { IconAlertCircle, IconCheck, IconTarget } from "../components/icons";
import type { Project, ResearchGap } from "../types";

/** Section 12/L: Gap Analyzer. Every candidate is deterministic (Cypher
 * queries over the knowledge graph) with human_verification_required
 * always true until a researcher explicitly verifies it here - never
 * auto-declared real. */
export default function GapsPage() {
  const toast = useToast();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [minPapers, setMinPapers] = useState(1);
  const [gaps, setGaps] = useState<ResearchGap[]>([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Project[]>("/projects").then((p) => {
      setProjects(p);
      if (p.length > 0) setProjectId(p[0].id);
    });
  }, []);

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    api
      .get<ResearchGap[]>(`/gaps?project_id=${projectId}`)
      .then(setGaps)
      .catch(() => setGaps([]))
      .finally(() => setLoading(false));
  }, [projectId]);

  async function analyze() {
    if (!projectId) return;
    setAnalyzing(true);
    setError(null);
    try {
      const found = await api.post<ResearchGap[]>("/gaps/analyze", { project_id: projectId, min_papers: minPapers });
      setGaps((prev) => [...found, ...prev]);
      toast.success(found.length > 0 ? `${found.length} candidate gap(s) detected.` : "No new gaps detected.");
    } catch (err) {
      if (err instanceof ApiError && err.status === 503) {
        setError(
          "Knowledge graph unavailable: no Neo4j instance reachable in this environment. " +
          "This is an honest failure (Section 81) — the platform never fabricates a gap-candidate list."
        );
      } else {
        setError(err instanceof ApiError ? err.message : "Gap analysis failed.");
      }
    } finally {
      setAnalyzing(false);
    }
  }

  async function verify(gapId: string, verified: boolean) {
    try {
      const updated = await api.post<ResearchGap>(`/gaps/${gapId}/verify`, {
        verified,
        rationale: verified ? "Confirmed after manual literature review." : "Not confirmed on review.",
      });
      setGaps((prev) => prev.map((g) => (g.id === gapId ? updated : g)));
      toast.success(verified ? "Gap marked human-verified." : "Gap marked not verified.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Failed to record verification.");
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Gap Analyzer</h2>
          <div className="subtitle">
            Deterministic Cypher queries surface candidate research gaps from the knowledge graph.
            Every candidate requires your explicit verification before it can back a hypothesis.
          </div>
        </div>
      </div>

      <Card>
        <div className="field-row">
          <div>
            <label>Project</label>
            <select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
              {projects.length === 0 && <option value="">No projects yet</option>}
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.title}</option>
              ))}
            </select>
          </div>
          <div style={{ maxWidth: 160 }}>
            <label>Min papers threshold</label>
            <input type="number" min={1} value={minPapers} onChange={(e) => setMinPapers(parseInt(e.target.value, 10) || 1)} />
          </div>
        </div>
        <button onClick={analyze} disabled={analyzing || !projectId} style={{ marginTop: 14 }}>
          {analyzing && <span className="spinner" />}
          <IconTarget size={14} />
          Run gap analysis
        </button>
      </Card>

      {error && (
        <div className="error-banner">
          <IconAlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {loading && <Card><SkeletonRows rows={3} height={60} /></Card>}

      {!loading && gaps.length === 0 && !error && (
        <Card>
          <EmptyState
            icon={<IconTarget size={30} />}
            title="No gaps recorded yet"
            description="Run an analysis to detect sparsely-studied method/dataset combinations and missing baselines in this project's literature."
          />
        </Card>
      )}

      {!loading &&
        gaps.map((g) => (
          <Card key={g.id}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "flex-start" }}>
              <div style={{ minWidth: 0, flex: 1 }}>
                <div className="btn-row" style={{ marginBottom: 8 }}>
                  <Badge tone="gold">{g.category.replace(/_/g, " ")}</Badge>
                  <span className="tiny faint">confidence {(g.confidence * 100).toFixed(0)}%</span>
                  {g.human_verified ? (
                    <Badge tone="ok">human-verified</Badge>
                  ) : (
                    <Badge tone="warn">unverified</Badge>
                  )}
                </div>
                <p style={{ margin: 0, fontSize: 13, lineHeight: 1.55 }}>{g.description}</p>
              </div>
              <div className="btn-row" style={{ flexShrink: 0 }}>
                <button className="secondary small" onClick={() => verify(g.id, true)} disabled={g.human_verified}>
                  <IconCheck size={13} />
                  Verify
                </button>
                <button className="ghost small" onClick={() => verify(g.id, false)}>
                  Dismiss
                </button>
              </div>
            </div>
          </Card>
        ))}

      {projects.length === 0 && !loading && (
        <p className="muted tiny">No projects yet — <Link to="/">create one on the dashboard</Link> first.</p>
      )}
    </div>
  );
}
