import type { Domain } from "../types";

export const DOMAIN_LABEL: Record<Domain, string> = {
  AI: "AI",
  CYBERSECURITY: "Cybersecurity",
  QUANTUM: "Quantum",
  PQC: "Post-Quantum Crypto",
};

export const DOMAIN_VAR: Record<Domain, string> = {
  AI: "var(--domain-ai)",
  CYBERSECURITY: "var(--domain-cybersecurity)",
  QUANTUM: "var(--domain-quantum)",
  PQC: "var(--domain-pqc)",
};
