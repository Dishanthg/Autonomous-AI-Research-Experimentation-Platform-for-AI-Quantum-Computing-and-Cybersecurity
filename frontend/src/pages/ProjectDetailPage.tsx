import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { Card } from "../components/Card";
import { Badge, DomainTag } from "../components/Badge";
import { EmptyState, SkeletonRows } from "../components/EmptyState";
import { useToast } from "../components/Toast";
import { IconArrowRight, IconClipboard, IconGitBranch, IconPlus } from "../components/icons";
import type { Project, ResearchQuestion, Hypothesis, Experiment, QualityCheck, Critique } from "../types";

export default function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const toast = useToast();
  const [project, setProject] = useState<Project | null>(null);
  const [questions, setQuestions] = useState<ResearchQuestion[]>([]);
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [nullH, setNullH] = useState("");
  const [altH, setAltH] = useState("");
  const [metric, setMetric] = useState("f1");
  const [baseline, setBaseline] = useState("rule_based");
  const [alpha, setAlpha] = useState(0.05);
  const [minEffect, setMinEffect] = useState(0.2);
  const [busy, setBusy] = useState(false);
  const [qcResult, setQcResult] = useState<Record<string, QualityCheck>>({});
  const [critiqueResult, setCritiqueResult] = useState<Record<string, Critique>>({});

  async function load() {
    if (!projectId) return;
    try {
      const [p, qs] = await Promise.all([
        api.get<Project>(`/projects/${projectId}`),
        api.get<ResearchQuestion[]>(`/projects/${projectId}/questions`),
      ]);
      setProject(p);
      setQuestions(qs);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load project.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function createHypothesis(e: React.FormEvent) {
    e.preventDefault();
    if (!projectId) return;
    setBusy(true);
    try {
      const hyp = await api.post<Hypothesis>("/hypotheses", {
        project_id: projectId,
        null_hypothesis: nullH,
        alternative_hypothesis: altH,
        independent_variables: ["method"],
        dependent_variables: [metric],
        baseline,
        evaluation_metric: metric,
        potential_confounders: ["class_imbalance"],
        decision_rule: { metric, alpha, min_effect_size: minEffect, direction: "greater" },
        generated_by: "human",
      });
      setHypotheses((prev) => [...prev, hyp]);
      setNullH("");
      setAltH("");
      setShowForm(false);
      toast.success("Hypothesis pre-registered.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Failed to create hypothesis.");
    } finally {
      setBusy(false);
    }
  }

  async function runQualityCheck(hypId: string) {
    const result = await api.post<QualityCheck>(`/hypotheses/${hypId}/quality-check`);
    setQcResult((prev) => ({ ...prev, [hypId]: result }));
    toast[result.passed ? "success" : "info"](
      result.passed ? "Quality check passed." : `Quality check: ${result.score}/${result.max_score}.`
    );
  }

  async function runCritique(hypId: string) {
    const result = await api.post<Critique>(`/hypotheses/${hypId}/critique`);
    setCritiqueResult((prev) => ({ ...prev, [hypId]: result }));
  }

  async function createExperiment(hypId: string) {
    if (!projectId || !project) return;
    const exp = await api.post<Experiment>("/experiments", {
      project_id: projectId,
      hypothesis_id: hypId,
      domain: project.domain,
      objective: `Test hypothesis ${hypId}`,
      num_runs_planned: 5,
    });
    setExperiments((prev) => [...prev, exp]);
    toast.success("Experiment created — configure it to continue.");
  }

  if (loading) {
    return (
      <div>
        <div className="skeleton" style={{ height: 26, width: 280, marginBottom: 20 }} />
        <Card><SkeletonRows rows={3} /></Card>
      </div>
    );
  }

  if (!project) return <div className="main">{error && <div className="error-banner">{error}</div>}</div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="btn-row" style={{ marginBottom: 6 }}>
            <DomainTag domain={project.domain} />
          </div>
          <h2>{project.title}</h2>
          {project.objectives && <div className="subtitle">{project.objectives}</div>}
        </div>
        <Link to={`/projects/${project.id}/lineage`}>
          <button className="secondary"><IconGitBranch size={14} />Research lineage</button>
        </Link>
      </div>
      {error && <div className="error-banner">{error}</div>}

      <Card title="Research questions">
        {questions.length === 0 ? (
          <p className="muted tiny">None yet.</p>
        ) : (
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {questions.map((q) => (
              <li key={q.id} style={{ marginBottom: 4, fontSize: 13 }}>
                {q.question_text} {q.is_primary && <Badge tone="ok">primary</Badge>}
              </li>
            ))}
          </ul>
        )}
      </Card>

      <div className="card-header" style={{ marginBottom: -4 }}>
        <h3 style={{ marginTop: 24 }}>Hypotheses ({hypotheses.length})</h3>
        {hypotheses.length > 0 && (
          <button onClick={() => setShowForm((s) => !s)}><IconPlus size={13} />New hypothesis</button>
        )}
      </div>

      {showForm && (
        <Card>
          <p className="tiny muted" style={{ marginTop: 0 }}>
            Pre-registered decision rule — fixed before any experiment runs, evaluated strictly against it later.
          </p>
          <form onSubmit={createHypothesis}>
            <label>Null hypothesis (H0)</label>
            <textarea value={nullH} onChange={(e) => setNullH(e.target.value)} required rows={2} />
            <label>Alternative hypothesis (H1)</label>
            <textarea value={altH} onChange={(e) => setAltH(e.target.value)} required rows={2} />
            <div className="field-row">
              <div>
                <label>Evaluation metric</label>
                <input value={metric} onChange={(e) => setMetric(e.target.value)} />
              </div>
              <div>
                <label>Baseline</label>
                <input value={baseline} onChange={(e) => setBaseline(e.target.value)} />
              </div>
            </div>
            <div className="field-row">
              <div>
                <label>Alpha</label>
                <input type="number" step="0.01" value={alpha} onChange={(e) => setAlpha(parseFloat(e.target.value))} />
              </div>
              <div>
                <label>Min effect size</label>
                <input type="number" step="0.05" value={minEffect} onChange={(e) => setMinEffect(parseFloat(e.target.value))} />
              </div>
            </div>
            <button type="submit" disabled={busy} style={{ marginTop: 14 }}>
              {busy && <span className="spinner" />}Create hypothesis
            </button>
          </form>
        </Card>
      )}

      {hypotheses.length === 0 && !showForm && (
        <Card>
          <EmptyState
            icon={<IconClipboard size={28} />}
            title="No hypotheses yet"
            description="Pre-register a null/alternative hypothesis pair with a fixed decision rule before running any experiment."
            action={<button onClick={() => setShowForm(true)}><IconPlus size={14} />New hypothesis</button>}
          />
        </Card>
      )}

      {hypotheses.map((h) => (
        <Card key={h.id}>
          <div><strong>H1:</strong> {h.alternative_hypothesis}</div>
          <div className="muted tiny" style={{ marginTop: 4 }}>
            Status: <Badge tone="muted">{h.status}</Badge>
            {h.quality_score != null && <span style={{ marginLeft: 6 }}>quality {h.quality_score}/8</span>}
          </div>
          <div className="btn-row" style={{ marginTop: 12 }}>
            <button className="secondary small" onClick={() => runQualityCheck(h.id)}>Quality check</button>
            <button className="secondary small" onClick={() => runCritique(h.id)}>Critique</button>
            <button className="small" onClick={() => createExperiment(h.id)}>Create experiment</button>
          </div>
          {qcResult[h.id] && (
            <div style={{ marginTop: 10 }}>
              <Badge tone={qcResult[h.id].passed ? "ok" : "danger"}>
                {qcResult[h.id].score}/{qcResult[h.id].max_score} {qcResult[h.id].passed ? "PASSED" : "FAILED"}
              </Badge>
            </div>
          )}
          {critiqueResult[h.id] && (
            <ul style={{ fontSize: 12.5, marginTop: 10, paddingLeft: 18 }}>
              {critiqueResult[h.id].objections.map((o, i) => (
                <li key={i} style={{ marginBottom: 4 }}>
                  <Badge tone={o.severity === "blocking" ? "danger" : "warn"}>{o.severity}</Badge> {o.message}
                </li>
              ))}
              {critiqueResult[h.id].objections.length === 0 && <li className="muted">No objections.</li>}
            </ul>
          )}
        </Card>
      ))}

      {experiments.length > 0 && (
        <Card title={`Experiments (${experiments.length})`}>
          {experiments.map((e) => (
            <div key={e.id} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              <span>{e.objective} <Badge tone="muted">{e.status}</Badge></span>
              <Link to={`/experiments/${e.id}/approve`} className="tiny">
                Configure &amp; approve <IconArrowRight size={12} style={{ verticalAlign: "-2px" }} />
              </Link>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}
