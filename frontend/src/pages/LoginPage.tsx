import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";
import { IconAlertCircle, IconAtom, IconCpu, IconLock, IconShield } from "../components/icons";

const DOMAINS = [
  { icon: IconCpu, color: "var(--domain-ai)", name: "AI", desc: "Model comparison, ablations, evidence-grounded claims" },
  { icon: IconShield, color: "var(--domain-cybersecurity)", name: "Cybersecurity", desc: "Intrusion detection, fusion scoring, threat models" },
  { icon: IconAtom, color: "var(--domain-quantum)", name: "Quantum computing", desc: "Circuit simulation, noise ablation, Grover/QFT" },
  { icon: IconLock, color: "var(--domain-pqc)", name: "Post-quantum crypto", desc: "Signing latency vs. classical, algorithm benchmarks" },
];

export default function LoginPage() {
  const { login, register, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("RESEARCHER");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (isAuthenticated) navigate("/");
  }, [isAuthenticated, navigate]);

  if (isAuthenticated) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "register") {
        await register(email, password, fullName, role);
      }
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <div className="auth-side">
          <div className="auth-brand">
            <div className="brand-mark" style={{ width: 34, height: 34, fontSize: 15 }}>RQ</div>
            <div>
              <div className="brand-name" style={{ fontSize: 15 }}>ResearchMind-Q</div>
              <div className="brand-tagline">Evidence-grounded research</div>
            </div>
          </div>
          <div className="auth-side-lede">
            Pre-registered hypotheses, sandboxed execution, and statistically
            grounded conclusions across four research domains.
          </div>
          <div className="auth-domain-list">
            {DOMAINS.map((d) => (
              <div className="auth-domain" key={d.name}>
                <div className="auth-domain-icon" style={{ color: d.color }}>
                  <d.icon size={15} />
                </div>
                <div>
                  <div className="auth-domain-name">{d.name}</div>
                  <div className="auth-domain-desc">{d.desc}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="auth-side-foot">
            <span className="badge-dot" />
            Human approval gates on every experiment run
          </div>
        </div>

        <div className="auth-form-col">
          {error && (
            <div className="error-banner">
              <IconAlertCircle size={15} />
              <span>{error}</span>
            </div>
          )}

          <h2 style={{ marginBottom: 2 }}>{mode === "login" ? "Log in" : "Create your account"}</h2>
          <div className="subtitle" style={{ marginBottom: 18 }}>
            {mode === "login" ? "Welcome back to your research workspace." : "Set up access to the research workspace."}
          </div>

          <form onSubmit={handleSubmit}>
            {mode === "register" && (
              <>
                <label>Full name</label>
                <input value={fullName} onChange={(e) => setFullName(e.target.value)} required autoFocus />
                <label>Role</label>
                <select value={role} onChange={(e) => setRole(e.target.value)}>
                  <option value="RESEARCHER">Researcher</option>
                  <option value="VIEWER">Viewer</option>
                  <option value="ADMIN">Admin</option>
                </select>
              </>
            )}
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@lab.org" />
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="••••••••" />
            <button type="submit" disabled={busy} style={{ width: "100%", marginTop: 18 }}>
              {busy && <span className="spinner" />}
              {mode === "login" ? "Log in" : "Create account & log in"}
            </button>
          </form>

          <div className="auth-toggle">
            {mode === "login" ? (
              <>No account yet? <button onClick={() => setMode("register")}>Register</button></>
            ) : (
              <>Already registered? <button onClick={() => setMode("login")}>Log in</button></>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
