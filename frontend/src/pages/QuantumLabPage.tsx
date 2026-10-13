import { useState } from "react";
import { api, ApiError } from "../api/client";
import { Card, StatTile } from "../components/Card";
import { Badge } from "../components/Badge";
import { useToast } from "../components/Toast";
import { IconActivity, IconAtom } from "../components/icons";
import type { QuantumRunResponse } from "../types";

/** Section 52: Quantum Lab UI. Every result is labeled SIMULATOR vs REAL
 * HARDWARE from the backend's own record - this build only ever produces
 * SIMULATOR results (Section 27/59: no hardware wiring exists). */
export default function QuantumLabPage() {
  const toast = useToast();
  const [algorithm, setAlgorithm] = useState<"bell_state" | "grover" | "qft">("bell_state");
  const [nQubits, setNQubits] = useState(3);
  const [markedState, setMarkedState] = useState("101");
  const [shots, setShots] = useState(2000);
  const [noiseRate, setNoiseRate] = useState<number | "">("");
  const [result, setResult] = useState<QuantumRunResponse | null>(null);
  const [noisyResult, setNoisyResult] = useState<QuantumRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    setResult(null);
    setNoisyResult(null);
    try {
      const payload: Record<string, unknown> = { algorithm, n_qubits: nQubits, shots };
      if (algorithm === "grover") payload.marked_state = markedState;

      const ideal = await api.post<QuantumRunResponse>("/quantum/run", payload);
      setResult(ideal);

      if (noiseRate !== "") {
        const noisy = await api.post<QuantumRunResponse>("/quantum/run", { ...payload, noise_error_rate: noiseRate });
        setNoisyResult(noisy);
      }
      toast.success("Circuit executed on the Aer simulator.");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Quantum run failed.";
      setError(msg);
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  }

  function renderResult(label: string, r: QuantumRunResponse) {
    const counts = Object.entries(r.measurement_counts).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const maxCount = Math.max(...counts.map(([, v]) => v), 1);
    return (
      <Card key={label} title={label}>
        <div className="btn-row" style={{ marginBottom: 12 }}>
          <Badge tone="ok">{r.backend_type}</Badge>
          <Badge tone="muted">{r.backend_name}</Badge>
          {r.noise_model && <Badge tone="warn">{r.noise_model}</Badge>}
        </div>

        <div className="grid-3" style={{ marginBottom: 14 }}>
          <StatTile label="Circuit depth" value={r.circuit_depth} />
          <StatTile label="Exec. time" value={`${(r.execution_time_seconds * 1000).toFixed(1)}ms`} />
          {r.success_probability != null ? (
            <StatTile label="Success prob." value={`${(r.success_probability * 100).toFixed(1)}%`} />
          ) : (
            <StatTile label="Shots" value={r.shots} />
          )}
        </div>

        <div className="tiny faint" style={{ textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 650, marginBottom: 8 }}>
          Measurement distribution
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {counts.map(([bitstring, count]) => (
            <div key={bitstring} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span className="mono tiny" style={{ width: 70, flexShrink: 0 }}>{bitstring}</span>
              <div style={{ flex: 1, background: "var(--surface-2)", borderRadius: 4, overflow: "hidden", height: 16 }}>
                <div
                  style={{
                    width: `${(count / maxCount) * 100}%`, height: "100%",
                    background: bitstring === markedState && algorithm === "grover" ? "var(--gold)" : "var(--accent)",
                    transition: "width 0.3s ease",
                  }}
                />
              </div>
              <span className="mono tiny faint" style={{ width: 44, textAlign: "right" }}>{count}</span>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Quantum Lab</h2>
          <div className="subtitle">
            Real Qiskit Aer simulations (Section 25-28). No fabricated results — every run is honestly
            labeled SIMULATOR, never HARDWARE.
          </div>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <Card>
        <form onSubmit={run}>
          <div className="field-row">
            <div>
              <label>Algorithm</label>
              <select value={algorithm} onChange={(e) => setAlgorithm(e.target.value as typeof algorithm)}>
                <option value="bell_state">Bell state (Q1)</option>
                <option value="grover">Grover search (Q2)</option>
                <option value="qft">Quantum Fourier Transform (Q3)</option>
              </select>
            </div>
            {algorithm !== "bell_state" && (
              <div style={{ maxWidth: 140 }}>
                <label>Qubits</label>
                <input type="number" min={1} max={6} value={nQubits} onChange={(e) => setNQubits(parseInt(e.target.value, 10))} />
              </div>
            )}
            {algorithm === "grover" && (
              <div>
                <label>Marked state <span className="hint">(bitstring)</span></label>
                <input value={markedState} onChange={(e) => setMarkedState(e.target.value)} className="mono" />
              </div>
            )}
          </div>
          <div className="field-row">
            <div>
              <label>Shots</label>
              <input type="number" min={100} step={100} value={shots} onChange={(e) => setShots(parseInt(e.target.value, 10))} />
            </div>
            <div>
              <label>Noise comparison <span className="hint">(depolarizing rate, optional)</span></label>
              <input
                type="number" step="0.01" min={0} max={1} placeholder="e.g. 0.05"
                value={noiseRate} onChange={(e) => setNoiseRate(e.target.value === "" ? "" : parseFloat(e.target.value))}
              />
            </div>
          </div>
          <button type="submit" disabled={busy} style={{ marginTop: 14 }}>
            {busy ? <span className="spinner" /> : <IconActivity size={14} />}
            Run on simulator
          </button>
        </form>
      </Card>

      {!result && !busy && (
        <Card>
          <div className="empty-state">
            <IconAtom size={30} />
            <div className="empty-title">No circuit run yet</div>
            <div className="empty-desc">Pick an algorithm above and run it against the Aer simulator to see a real measurement distribution.</div>
          </div>
        </Card>
      )}

      {result && renderResult("Ideal (no noise)", result)}
      {noisyResult && renderResult(`Noisy (${noisyResult.noise_model})`, noisyResult)}
    </div>
  );
}
