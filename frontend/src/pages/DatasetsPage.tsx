import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { Card } from "../components/Card";
import { Badge } from "../components/Badge";
import { EmptyState, SkeletonRows } from "../components/EmptyState";
import { useToast } from "../components/Toast";
import { IconDatabase, IconPlus } from "../components/icons";
import type { Dataset, DatasetVersion } from "../types";

/** Section 44/60: dataset registry. Registering a real DatasetVersion and
 * referencing it from an experiment config is what clears the
 * `reproducibility_limitation` finding the Limitation Detector otherwise
 * attaches to every run. */
export default function DatasetsPage() {
  const toast = useToast();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [versions, setVersions] = useState<Record<string, DatasetVersion[]>>({});
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [source, setSource] = useState("");
  const [license, setLicense] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);

  function load() {
    setLoading(true);
    api
      .get<Dataset[]>("/datasets")
      .then(setDatasets)
      .catch(() => setDatasets([]))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function toggleExpand(datasetId: string) {
    if (expanded === datasetId) {
      setExpanded(null);
      return;
    }
    setExpanded(datasetId);
    if (!versions[datasetId]) {
      try {
        const v = await api.get<DatasetVersion[]>(`/datasets/${datasetId}/versions`);
        setVersions((prev) => ({ ...prev, [datasetId]: v }));
      } catch {
        setVersions((prev) => ({ ...prev, [datasetId]: [] }));
      }
    }
  }

  async function createDataset(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/datasets", { name, source, license, description: description || null });
      toast.success(`Registered dataset "${name}".`);
      setName("");
      setSource("");
      setLicense("");
      setDescription("");
      setShowForm(false);
      load();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Failed to register dataset.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Dataset Registry</h2>
          <div className="subtitle">
            Every dataset an experiment uses, pinned with a real version and checksum — the record
            that turns "reproducibility_limitation" into a closed loop.
          </div>
        </div>
        <button onClick={() => setShowForm((s) => !s)}>
          <IconPlus size={14} />
          Register dataset
        </button>
      </div>

      {showForm && (
        <Card title="New dataset">
          <form onSubmit={createDataset}>
            <div className="field-row">
              <div>
                <label>Name</label>
                <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. breast_cancer" />
              </div>
              <div>
                <label>License</label>
                <input value={license} onChange={(e) => setLicense(e.target.value)} required placeholder="e.g. public domain" />
              </div>
            </div>
            <label>Source</label>
            <input value={source} onChange={(e) => setSource(e.target.value)} required placeholder="e.g. sklearn.datasets.load_breast_cancer" />
            <label>Description <span className="hint">(optional)</span></label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} />
            <div className="btn-row" style={{ marginTop: 14 }}>
              <button type="submit" disabled={busy}>{busy && <span className="spinner" />}Register</button>
              <button type="button" className="ghost" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </Card>
      )}

      {loading && <Card><SkeletonRows rows={3} height={50} /></Card>}

      {!loading && datasets.length === 0 && (
        <Card>
          <EmptyState
            icon={<IconDatabase size={30} />}
            title="No datasets registered"
            description="Register the datasets your experiments use — a pinned version and checksum makes each run's data provenance independently verifiable."
            action={<button onClick={() => setShowForm(true)}><IconPlus size={14} />Register dataset</button>}
          />
        </Card>
      )}

      {!loading &&
        datasets.map((d) => (
          <Card key={d.id} className="card-flush">
            <div
              style={{ padding: "16px 20px", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}
              onClick={() => toggleExpand(d.id)}
            >
              <div>
                <div style={{ fontWeight: 650, fontSize: 13.5 }}>{d.name}</div>
                <div className="tiny muted" style={{ marginTop: 2 }}>{d.source}</div>
              </div>
              <Badge tone="muted">{d.license}</Badge>
            </div>
            {expanded === d.id && (
              <div style={{ padding: "0 20px 18px", borderTop: "1px solid var(--border)" }}>
                {d.description && <p className="tiny muted" style={{ marginTop: 14 }}>{d.description}</p>}
                <div style={{ marginTop: 10 }}>
                  <div className="tiny faint" style={{ textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8, fontWeight: 650 }}>
                    Versions
                  </div>
                  {(versions[d.id] ?? []).length === 0 ? (
                    <p className="tiny faint">No versions registered yet.</p>
                  ) : (
                    <div className="table-wrap">
                      <table>
                        <thead><tr><th>Tag</th><th>Rows</th><th>Checksum</th></tr></thead>
                        <tbody>
                          {(versions[d.id] ?? []).map((v) => (
                            <tr key={v.id}>
                              <td className="mono">{v.version_tag}</td>
                              <td>{v.row_count ?? "—"}</td>
                              <td className="mono tiny faint">{v.checksum ? `${v.checksum.slice(0, 16)}…` : "—"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )}
          </Card>
        ))}
    </div>
  );
}
