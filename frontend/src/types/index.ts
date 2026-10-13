export type Domain = "AI" | "CYBERSECURITY" | "QUANTUM" | "PQC";
export type Role = "ADMIN" | "RESEARCHER" | "VIEWER";
export type HypothesisStatus =
  | "DRAFT" | "QUALITY_CHECKED" | "CRITIQUED" | "APPROVED" | "TESTING"
  | "SUPPORTED" | "NOT_SUPPORTED" | "INCONCLUSIVE";
export type ExperimentStatus =
  | "DRAFT" | "PLANNED" | "PENDING_APPROVAL" | "APPROVED" | "CODE_GENERATED"
  | "PENDING_EXECUTION_APPROVAL" | "RUNNING" | "COMPLETED" | "FAILED" | "ANALYZED"
  | "CRITIQUED" | "CONCLUDED";
export type RunStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "TIMEOUT" | "KILLED";
export type ConclusionStatus = "SUPPORTED" | "NOT_SUPPORTED" | "INCONCLUSIVE";

export interface Project {
  id: string;
  title: string;
  domain: Domain;
  owner_id: string;
  objectives?: string | null;
  conclusions?: string | null;
  limitations?: string | null;
  future_work?: string | null;
}

export interface ResearchQuestion {
  id: string;
  project_id: string;
  question_text: string;
  domain: Domain;
  is_primary: boolean;
}

export interface Hypothesis {
  id: string;
  project_id: string;
  null_hypothesis: string;
  alternative_hypothesis: string;
  independent_variables: string[];
  dependent_variables: string[];
  evaluation_metric: string;
  decision_rule: Record<string, unknown>;
  quality_score?: number | null;
  status: HypothesisStatus;
}

export interface QualityCheck {
  score: number;
  max_score: number;
  checks: Record<string, boolean>;
  passed: boolean;
}

export interface Objection {
  severity: string;
  category: string;
  message: string;
}

export interface Critique {
  objections: Objection[];
  has_blocking: boolean;
}

export interface Experiment {
  id: string;
  project_id: string;
  hypothesis_id: string;
  domain: Domain;
  objective: string;
  status: ExperimentStatus;
  num_runs_planned: number;
}

export interface ExperimentConfig {
  id: string;
  experiment_id: string;
  version: number;
  approved: boolean;
  approved_by_user_id?: string | null;
  num_runs: number;
  metrics_requested: string[];
}

export interface ExperimentRun {
  id: string;
  experiment_id: string;
  config_id: string;
  status: RunStatus;
  exit_code?: number | null;
  stdout?: string | null;
  stderr?: string | null;
  isolation_level?: string | null;
}

export interface Result {
  id: string;
  experiment_id: string;
  hypothesis_id: string;
  computed_by: string;
  conclusion_status?: ConclusionStatus | null;
  conclusion_rationale?: string | null;
  human_approved: boolean;
}

export interface StatisticalTest {
  metric_name: string;
  test_name: string;
  statistic?: number | null;
  p_value?: number | null;
  effect_size?: number | null;
  effect_size_type?: string | null;
  ci_lower?: number | null;
  ci_upper?: number | null;
  ci_level?: number | null;
}

export interface QuantumRunResponse {
  algorithm: string;
  backend_name: string;
  backend_type: "SIMULATOR" | "HARDWARE";
  shots: number;
  noise_model?: string | null;
  execution_time_seconds: number;
  circuit_depth: number;
  gate_count: Record<string, number>;
  measurement_counts: Record<string, number>;
  success_probability?: number | null;
  error_rate?: number | null;
}

export interface HealthStatus {
  status: string;
  checks: Record<string, string>;
}

export interface LineageRun {
  id: string;
  status: RunStatus;
  isolation_level?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  exit_code?: number | null;
}

export interface LineageStatisticalTest {
  metric_name: string;
  test_name: string;
  p_value?: number | null;
  effect_size?: number | null;
  effect_size_type?: string | null;
}

export interface LineageResult {
  id: string;
  conclusion_status?: ConclusionStatus | null;
  conclusion_rationale?: string | null;
  human_approved: boolean;
  statistical_tests: LineageStatisticalTest[];
}

export interface LineageExperiment {
  id: string;
  domain: Domain;
  objective: string;
  status: ExperimentStatus;
  runs: LineageRun[];
  results: LineageResult[];
  limitations: { category: string; description: string }[];
}

export interface LineageHypothesis {
  id: string;
  null_hypothesis: string;
  alternative_hypothesis: string;
  status: HypothesisStatus;
  experiments: LineageExperiment[];
}

export interface LineageQuestion {
  id: string;
  question_text: string;
  is_primary: boolean;
  hypotheses: LineageHypothesis[];
}

export interface ProjectLineage {
  project_id: string;
  project_title: string;
  questions: LineageQuestion[];
  unlinked_hypotheses: LineageHypothesis[];
}

export interface Paper {
  id: string;
  title: string;
  authors?: string[] | null;
  year?: number | null;
  venue?: string | null;
  doi?: string | null;
  url?: string | null;
  source: string;
  abstract?: string | null;
}

export interface ResearchGap {
  id: string;
  project_id: string;
  category: string;
  description: string;
  evidence?: Record<string, unknown> | null;
  confidence: number;
  human_verification_required: boolean;
  human_verified: boolean;
}

export interface Dataset {
  id: string;
  name: string;
  source: string;
  license: string;
  description?: string | null;
  features?: string[] | null;
  limitations?: string | null;
  citation?: string | null;
}

export interface DatasetVersion {
  id: string;
  dataset_id: string;
  version_tag: string;
  checksum?: string | null;
  preprocessing?: string | null;
  row_count?: number | null;
}
