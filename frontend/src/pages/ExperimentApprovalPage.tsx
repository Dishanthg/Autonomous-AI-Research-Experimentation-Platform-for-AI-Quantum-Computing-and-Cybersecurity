import { useState } from "react";
import { useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { Badge, StatusBadge } from "../components/Badge";
import { Card } from "../components/Card";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { useToast } from "../components/Toast";
import { IconAlertCircle, IconAlertTriangle, IconCheck, IconTarget } from "../components/icons";
import type { ExperimentConfig, Critique, ExperimentRun, Result, StatisticalTest } from "../types";

/** Section 50: Experiment Approval UI. Shows the generated config, runs the
 * critic, and requires an explicit human action for both approval gates
 * before any sandbox execution occurs. */
export default function ExperimentApprovalPage() {
  const { experimentId } = useParams<{ experimentId: string }>();
  const toast = useToast();
  const [baseline, setBaseline] = useState("rule_based");
  const [proposed, setProposed] = useState("graph_enhanced_rf");
  const [numRuns, setNumRuns] = useState(5);
  const [config, setConfig] = useState<ExperimentConfig | null>(null);
  const [critique, setCritique] = useState<Critique | null>(null);
  const [run, setRun] = useState<ExperimentRun | null>(null);
  const [results, setResults] = useState<Result[]>([]);
  const [stats, setStats] = useState<StatisticalTest[]>([]);
  const [limitations, setLimitations] = useState<{ category: string; description: string }[]>([]);
  const [nextExperiments, setNextExperiments] = useState<{ category: string; description: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [confirmExecute, setConfirmExecute] = useState(false);
  const [busy, setBusy] = useState<"create" | "critique" | "approve" | "execute" | null>(null);

  const step = run ? 4 : config?.approved ? 3 : config ? 2 : 1;

  async function createConfig(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy("create");
    try {
      const c = await api.post<ExperimentConfig>(`/experiments/${experimentId}/configs`, {
        experiment_id: experimentId,
        baseline_spec: baseline,
        model_spec: proposed,
        random_seed: 42,
        num_runs: numRuns,
        metrics_requested: ["f1", "pr_auc"],
        resource_limits: { cpu: 1, memory: "512m", timeout_seconds: 120 },
        codegen_spec: { baseline, proposed, num_runs: numRuns, base_seed: 42 },
      });
      setConfig(c);
      setCritique(null);
      setRun(null);
      toast.success(`Config v${c.version} generated.`);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to create config.";
      setError(msg);
      toast.error(msg);
    } finally {
      setBusy(null);
    }
  }

  async function runCritique() {
    if (!config) return;
    setBusy("critique");
    try {
      const c = await api.post<Critique>(`/experiments/configs/${config.id}/critique`);
      setCritique(c);
      toast[c.has_blocking ? "info" : "success"](
        c.has_blocking ? "Critic raised blocking objections." : "Critic found no blocking objections."
      );
    } finally {
      setBusy(null);
    }
  }

  async function approve() {
    if (!config) return;
    setError(null);
    setBusy("approve");
    try {
      const c = await api.post<ExperimentConfig>(`/experiments/configs/${config.id}/approve`, {
        rationale: "Reviewed baseline, metrics, and sample size.",
      });
      setConfig(c);
      toast.success("Approved (Gate 1). Execution (Gate 2) is now available.");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Approval refused (see critic objections).";
      setError(msg);
      toast.error("Approval refused.");
    } finally {
      setBusy(null);
    }
  }

  async function execute() {
    if (!config) return;
    setConfirmExecute(false);
    setError(null);
    setBusy("execute");
    try {
      const r = await api.post<ExperimentRun>(`/experiments/configs/${config.id}/execute`, {
        rationale: "Executing approved config.",
      });
      setRun(r);
      const res = await api.get<Result[]>(`/experiments/${experimentId}/results`);
      setResults(res);
      if (res.length > 0) {
        const st = await api.get<StatisticalTest[]>(`/experiments/results/${res[res.length - 1].id}/statistics`);
        setStats(st);
        const [lims, nexts] = await Promise.all([
          api.get<{ category: string; description: string }[]>(`/experiments/${experimentId}/limitations`),
          api.get<{ category: string; description: string }[]>(`/experiments/${experimentId}/next-experiments`),
        ]);
        setLimitations(lims);
        setNextExperiments(nexts);
      }
      toast[r.status === "COMPLETED" ? "success" : "error"](`Run ${r.status.toLowerCase()}.`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 503) {
        setError(
          "Sandbox unavailable: no Docker daemon reachable in this environment. " +
          "This is the expected, honest failure mode (Rule 5) — execution never " +
          "falls back to running generated code unsandboxed."
        );
      } else {
        setError(err instanceof ApiError ? err.message : "Execution failed.");
      }
      toast.error("Execution failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Experiment Approval</h2>
          <div className="subtitle">Two human approval gates stand between a generated config and any code execution.</div>
        </div>
      </div>

      <Stepper step={step} />

      {error && (
        <div className="error-banner">
          <IconAlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      <Card title="1 · Configure (cybersecurity domain template)">
        <form onSubmit={createConfig}>
          <div className="field-row">
            <div>
              <label>Baseline detector</label>
              <select value={baseline} onChange={(e) => setBaseline(e.target.value)}>
                <option value="rule_based">Rule-based</option>
                <option value="logistic_regression">Logistic Regression</option>
                <option value="random_forest">Random Forest</option>
              </select>
            </div>
            <div>
              <label>Proposed method</label>
              <select value={proposed} onChange={(e) => setProposed(e.target.value)}>
                <option value="graph_enhanced_rf">Graph-enhanced Random Forest</option>
                <option value="random_forest">Random Forest</option>
                <option value="logistic_regression">Logistic Regression</option>
              </select>
            </div>
            <div style={{ maxWidth: 120 }}>
              <label>Runs</label>
              <input type="number" min={1} value={numRuns} onChange={(e) => setNumRuns(parseInt(e.target.value, 10))} />
            </div>
          </div>
          <button type="submit" disabled={busy === "create"} style={{ marginTop: 14 }}>
            {busy === "create" && <span className="spinner" />}Generate config
          </button>
        </form>
      </Card>

      {config && (
        <Card title="2 · Review & critique">
          <div className="btn-row" style={{ marginBottom: 12 }}>
            <span className="tiny muted">Config v{config.version} · {config.num_runs} runs · metrics: {config.metrics_requested.join(", ")}</span>
            <Badge tone={config.approved ? "ok" : "muted"}>{config.approved ? "approved" : "not approved"}</Badge>
          </div>
          <button className="secondary small" onClick={runCritique} disabled={busy === "critique"}>
            {busy === "critique" && <span className="spinner" />}Run critic
          </button>
          {critique && (
            <ul style={{ fontSize: 12.5, marginTop: 12, paddingLeft: 18 }}>
              {critique.objections.map((o, i) => (
                <li key={i} style={{ marginBottom: 5 }}>
                  <Badge tone={o.severity === "blocking" ? "danger" : "warn"}>{o.severity}</Badge> {o.message}
                </li>
              ))}
              {critique.objections.length === 0 && (
                <li className="muted" style={{ listStyle: "none", marginLeft: -18, display: "flex", gap: 6, alignItems: "center" }}>
                  <IconCheck size={13} /> No objections.
                </li>
              )}
            </ul>
          )}
          <div className="btn-row" style={{ marginTop: 14 }}>
            <button onClick={approve} disabled={config.approved || busy === "approve"}>
              {busy === "approve" && <span className="spinner" />}Approve (Gate 1)
            </button>
            <button
              className={config.approved ? "" : "secondary"}
              onClick={() => setConfirmExecute(true)}
              disabled={!config.approved || busy === "execute"}
            >
              {busy === "execute" && <span className="spinner" />}Execute (Gate 2)
            </button>
          </div>
        </Card>
      )}

      <ConfirmDialog
        open={confirmExecute}
        title="Execute this experiment?"
        description="This runs the generated code inside the sandboxed executor and records a real ExperimentRun. This action is audit-logged and cannot be undone."
        confirmLabel="Execute"
        busy={busy === "execute"}
        onConfirm={execute}
        onCancel={() => setConfirmExecute(false)}
      />

      {run && (
        <Card title="3 · Run">
          <div className="btn-row">
            <StatusBadge value={run.status} />
            {run.isolation_level && <Badge tone="muted">{run.isolation_level}</Badge>}
          </div>
          {run.stderr && <pre style={{ marginTop: 10 }}>{run.stderr}</pre>}
        </Card>
      )}

      {results.length > 0 && (
        <Card title="4 · Conclusion">
          {results.map((r) => (
            <div key={r.id} style={{ marginBottom: 12 }}>
              <StatusBadge value={r.conclusion_status ?? "PENDING"} />
              <p style={{ fontSize: 13, marginTop: 6 }}>{r.conclusion_rationale}</p>
            </div>
          ))}
          {stats.map((s, i) => (
            <div key={i} className="kv-row" style={{ borderTop: "1px solid var(--border)", paddingTop: 8, marginTop: 4 }}>
              <span className="k">{s.test_name}</span>
              <span className="v">
                p={s.p_value?.toFixed(4)} · effect={s.effect_size?.toFixed(3)} ({s.effect_size_type}) · CI[{s.ci_lower?.toFixed(3)}, {s.ci_upper?.toFixed(3)}]
              </span>
            </div>
          ))}
        </Card>
      )}

      {limitations.length > 0 && (
        <Card title="Limitations" action={<span className="tiny faint">deterministically detected</span>}>
          <ul style={{ fontSize: 13, margin: 0, paddingLeft: 18 }}>
            {limitations.map((l, i) => (
              <li key={i} style={{ marginBottom: 6, display: "flex", gap: 6, alignItems: "flex-start" }}>
                <IconAlertTriangle size={13} style={{ marginTop: 2, flexShrink: 0, color: "var(--warn)" }} />
                <span><Badge tone="warn">{l.category.replace(/_/g, " ")}</Badge> {l.description}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {nextExperiments.length > 0 && (
        <Card title="Proposed next experiments" action={<span className="tiny faint">requires your approval to act on</span>}>
          <ul style={{ fontSize: 13, margin: 0, paddingLeft: 18 }}>
            {nextExperiments.map((n, i) => (
              <li key={i} style={{ marginBottom: 6, display: "flex", gap: 6, alignItems: "flex-start" }}>
                <IconTarget size={13} style={{ marginTop: 2, flexShrink: 0, color: "var(--accent-strong)" }} />
                <span><Badge tone="muted">{n.category.replace(/_/g, " ")}</Badge> {n.description}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}

function Stepper({ step }: { step: number }) {
  const labels = ["Configure", "Critique", "Approve", "Execute"];
  return (
    <div className="btn-row" style={{ marginBottom: 20 }}>
      {labels.map((label, i) => {
        const n = i + 1;
        const active = n === step;
        const done = n < step;
        return (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div
              style={{
                width: 22, height: 22, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 11, fontWeight: 700, fontFamily: "var(--mono)",
                background: done ? "var(--ok-soft)" : active ? "var(--accent-soft)" : "var(--surface-2)",
                color: done ? "var(--ok)" : active ? "var(--accent-strong)" : "var(--text-faint)",
                border: `1px solid ${done ? "var(--ok)" : active ? "var(--accent)" : "var(--border)"}`,
              }}
            >
              {done ? <IconCheck size={11} /> : n}
            </div>
            <span className="tiny" style={{ color: active ? "var(--text)" : "var(--text-faint)", fontWeight: active ? 650 : 500 }}>
              {label}
            </span>
            {i < labels.length - 1 && <div style={{ width: 24, height: 1, background: "var(--border)" }} />}
          </div>
        );
      })}
    </div>
  );
}
