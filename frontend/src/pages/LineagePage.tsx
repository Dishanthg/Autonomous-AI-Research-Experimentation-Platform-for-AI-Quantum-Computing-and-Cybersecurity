import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { Card } from "../components/Card";
import { StatusBadge } from "../components/Badge";
import { EmptyState, SkeletonRows } from "../components/EmptyState";
import { IconGitBranch } from "../components/icons";
import type { ProjectLineage, LineageHypothesis } from "../types";

/** Section 43/53/90: a navigable Question -> Hypothesis -> Experiment ->
 * Result -> Conclusion -> Limitation -> Next-Question chain, rendered as a
 * nested list (a graph visualization is future work). */
export default function LineagePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [lineage, setLineage] = useState<ProjectLineage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    api
      .get<ProjectLineage>(`/projects/${projectId}/lineage`)
      .then(setLineage)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load lineage."));
  }, [projectId]);

  if (error) return <div><div className="error-banner">{error}</div></div>;
  if (!lineage) return <Card><SkeletonRows rows={4} /></Card>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Research Lineage</h2>
          <div className="subtitle">
            {lineage.project_title} — <Link to={`/projects/${lineage.project_id}`}>back to project</Link>
          </div>
        </div>
      </div>

      {lineage.questions.length === 0 && lineage.unlinked_hypotheses.length === 0 && (
        <Card>
          <EmptyState
            icon={<IconGitBranch size={28} />}
            title="Nothing to trace yet"
            description="Once this project has a research question, hypothesis, and experiment, the full chain will appear here."
          />
        </Card>
      )}

      {lineage.questions.map((q) => (
        <Card key={q.id} title={q.question_text}>
          {q.is_primary && <span className="badge ok" style={{ marginBottom: 8 }}>primary question</span>}
          {q.hypotheses.length === 0 ? (
            <p className="muted">No hypotheses yet for this question.</p>
          ) : (
            q.hypotheses.map((h) => <HypothesisNode key={h.id} hypothesis={h} />)
          )}
        </Card>
      ))}

      {lineage.unlinked_hypotheses.length > 0 && (
        <Card title="Hypotheses not linked to a research question">
          {lineage.unlinked_hypotheses.map((h) => (
            <HypothesisNode key={h.id} hypothesis={h} />
          ))}
        </Card>
      )}
    </div>
  );
}

function HypothesisNode({ hypothesis }: { hypothesis: LineageHypothesis }) {
  return (
    <div className="timeline-node" style={{ marginBottom: 20, paddingBottom: 2 }}>
      <div>
        <strong>H1:</strong> {hypothesis.alternative_hypothesis}
      </div>
      <div className="muted" style={{ fontSize: 12, marginBottom: 10 }}>
        Status: <StatusBadge value={hypothesis.status} />
      </div>
      {hypothesis.experiments.length === 0 ? (
        <p className="muted" style={{ fontSize: 12 }}>No experiments yet.</p>
      ) : (
        hypothesis.experiments.map((e) => (
          <div key={e.id} className="timeline-node" style={{ marginBottom: 14 }}>
            <div>
              <Link to={`/experiments/${e.id}/approve`}>{e.objective}</Link>{" "}
              <span className="badge muted">{e.domain}</span> <StatusBadge value={e.status} />
            </div>

            {e.runs.map((r) => (
              <div key={r.id} className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                Run <code>{r.id.slice(0, 8)}</code>: <StatusBadge value={r.status} />{" "}
                {r.isolation_level && <span className="badge muted">{r.isolation_level}</span>}
              </div>
            ))}

            {e.results.map((res) => (
              <div key={res.id} style={{ marginTop: 6, fontSize: 12 }}>
                Conclusion:{" "}
                {res.conclusion_status ? <StatusBadge value={res.conclusion_status} /> : <span className="muted">pending</span>}
                {res.conclusion_rationale && (
                  <div className="muted" style={{ marginTop: 2 }}>{res.conclusion_rationale}</div>
                )}
                {res.statistical_tests.map((st, i) => (
                  <div key={i} className="muted" style={{ marginTop: 2 }}>
                    {st.metric_name}: {st.test_name}, p={st.p_value?.toFixed(4) ?? "n/a"}, effect=
                    {st.effect_size?.toFixed(3) ?? "n/a"} ({st.effect_size_type ?? "n/a"})
                  </div>
                ))}
              </div>
            ))}

            {e.limitations.length > 0 && (
              <ul style={{ fontSize: 12, marginTop: 6 }}>
                {e.limitations.map((lim, i) => (
                  <li key={i}>
                    <span className="badge warn">{lim.category}</span> {lim.description}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))
      )}
    </div>
  );
}
