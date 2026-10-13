import { Routes, Route, Navigate, NavLink } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { ToastProvider } from "./components/Toast";
import { IconAtom, IconClipboard, IconDatabase, IconFileText, IconGrid, IconLogOut, IconTarget } from "./components/icons";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import ProjectDetailPage from "./pages/ProjectDetailPage";
import LineagePage from "./pages/LineagePage";
import ExperimentApprovalPage from "./pages/ExperimentApprovalPage";
import QuantumLabPage from "./pages/QuantumLabPage";
import LiteraturePage from "./pages/LiteraturePage";
import GapsPage from "./pages/GapsPage";
import DatasetsPage from "./pages/DatasetsPage";
import AuditLogPage from "./pages/AuditLogPage";

function Shell({ children }: { children: React.ReactNode }) {
  const { logout, user } = useAuth();
  const initials = (user?.full_name || user?.email || "?")
    .split(" ")
    .map((s) => s[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">RQ</div>
          <div>
            <div className="brand-name">ResearchMind-Q</div>
            <div className="brand-tagline">Evidence-grounded research</div>
          </div>
        </div>

        <div className="nav-section-label">Workspace</div>
        <nav>
          <NavLink to="/" end><IconGrid size={15} />Dashboard</NavLink>
        </nav>

        <div className="nav-section-label">Research tools</div>
        <nav>
          <NavLink to="/literature"><IconFileText size={15} />Literature</NavLink>
          <NavLink to="/gaps"><IconTarget size={15} />Gap Analyzer</NavLink>
          <NavLink to="/datasets"><IconDatabase size={15} />Datasets</NavLink>
          <NavLink to="/quantum-lab"><IconAtom size={15} />Quantum Lab</NavLink>
        </nav>

        <div className="nav-section-label">System</div>
        <nav>
          <NavLink to="/audit-log"><IconClipboard size={15} />Audit Log</NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="user-chip">
            <div className="user-avatar">{initials}</div>
            <div className="user-meta">
              <div className="user-name">{user?.full_name ?? "…"}</div>
              <div className="user-role">{(user?.role ?? "").toLowerCase()}</div>
            </div>
          </div>
          <button className="logout-btn" onClick={logout}>
            <IconLogOut size={14} />
            Log out
          </button>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Shell>{children}</Shell>;
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<RequireAuth><DashboardPage /></RequireAuth>} />
          <Route path="/projects/:projectId" element={<RequireAuth><ProjectDetailPage /></RequireAuth>} />
          <Route path="/projects/:projectId/lineage" element={<RequireAuth><LineagePage /></RequireAuth>} />
          <Route path="/experiments/:experimentId/approve" element={<RequireAuth><ExperimentApprovalPage /></RequireAuth>} />
          <Route path="/literature" element={<RequireAuth><LiteraturePage /></RequireAuth>} />
          <Route path="/gaps" element={<RequireAuth><GapsPage /></RequireAuth>} />
          <Route path="/datasets" element={<RequireAuth><DatasetsPage /></RequireAuth>} />
          <Route path="/quantum-lab" element={<RequireAuth><QuantumLabPage /></RequireAuth>} />
          <Route path="/audit-log" element={<RequireAuth><AuditLogPage /></RequireAuth>} />
        </Routes>
      </ToastProvider>
    </AuthProvider>
  );
}
