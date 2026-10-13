import { createContext, useCallback, useContext, useRef, useState } from "react";
import { IconAlertCircle, IconCheck, IconInfo, IconX } from "./icons";

type ToastKind = "ok" | "error" | "info";
interface ToastItem { id: number; kind: ToastKind; message: string; }

interface ToastApi {
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
}

const ToastContext = createContext<ToastApi | null>(null);

const ICONS: Record<ToastKind, React.ComponentType<{ size?: number }>> = {
  ok: IconCheck,
  error: IconAlertCircle,
  info: IconInfo,
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const idRef = useRef(0);

  const push = useCallback((kind: ToastKind, message: string) => {
    const id = ++idRef.current;
    setItems((prev) => [...prev, { id, kind, message }]);
    setTimeout(() => setItems((prev) => prev.filter((t) => t.id !== id)), 4500);
  }, []);

  const api: ToastApi = {
    success: (m) => push("ok", m),
    error: (m) => push("error", m),
    info: (m) => push("info", m),
  };

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="toast-stack">
        {items.map((t) => {
          const Icon = ICONS[t.kind];
          return (
            <div className={`toast ${t.kind}`} key={t.id}>
              <Icon size={16} />
              <span>{t.message}</span>
              <button
                className="toast-close"
                aria-label="Dismiss"
                onClick={() => setItems((prev) => prev.filter((i) => i.id !== t.id))}
              >
                <IconX size={13} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
