export type Severity = "high" | "medium" | "low";

export type Verdict =
  | "suitable"
  | "partially_suitable"
  | "not_suitable"
  | "unknown";

export interface ContradictionCounts {
  high?: number;
  medium?: number;
  low?: number;
}

export interface ContradictionItem {
  severity?: Severity | string;
  code?: string;
  title?: string;
  description?: string;
  fields?: string[];
  source?: "rule" | "llm" | string;
}

export interface Contradictions {
  has_contradictions?: boolean;
  counts?: ContradictionCounts;
  items?: ContradictionItem[];
  summary?: string;
}

export interface CandidateFacts {
  full_name?: string;
  position_name?: string;
  department?: string;
  age?: number | null;
  career_start?: string | null;
  career_span_years?: number | null;
  has_job?: boolean;
  education_count?: number;
  experience_count?: number;
}

export interface Fit {
  verdict?: Verdict | string;
  score?: number | null;
  summary?: string;
  strengths?: string[];
  gaps?: string[];
  matched_requirements?: string[];
  unmatched_requirements?: string[];
  relevant_experience_years?: number | null;
  required_experience_years?: number | null;
  confidence?: string | null;
}

export interface AnalysisError {
  stage?: string;
  message?: string;
}

export interface ScreeningReport {
  generated_at?: string;
  model?: string;
  candidate?: CandidateFacts;
  contradictions?: Contradictions;
  fit?: Fit;
  recommendation?: string;
  analysis_errors?: AnalysisError[];
}

export interface HistoryEntry {
  id: string;
  createdAt: string;
  candidate: string;
  position: string;
  verdict: string;
  verdictLabel: string;
  score: number | null;
  high: number;
  medium: number;
  low: number;
}
