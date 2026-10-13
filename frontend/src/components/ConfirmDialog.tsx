import { useEffect } from "react";
import { IconAlertTriangle } from "./icons";

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  danger = false,
  busy = false,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  danger?: boolean;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onCancel();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
        <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
          <div
            style={{
              width: 34, height: 34, borderRadius: 9, flexShrink: 0,
              display: "flex", alignItems: "center", justifyContent: "center",
              background: danger ? "var(--danger-soft)" : "var(--warn-soft)",
              color: danger ? "var(--danger)" : "var(--warn)",
            }}
          >
            <IconAlertTriangle size={18} />
          </div>
          <div style={{ flex: 1 }}>
            <h3 style={{ marginBottom: 6 }}>{title}</h3>
            <p className="muted tiny" style={{ margin: 0, lineHeight: 1.55 }}>{description}</p>
          </div>
        </div>
        <div className="btn-row" style={{ marginTop: 20, justifyContent: "flex-end" }}>
          <button className="secondary" onClick={onCancel} disabled={busy}>Cancel</button>
          <button className={danger ? "danger" : ""} onClick={onConfirm} disabled={busy}>
            {busy && <span className="spinner" />}
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
