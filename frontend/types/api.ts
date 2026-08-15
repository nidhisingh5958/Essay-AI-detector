/**
 * Types mirroring backend/app/models/api_schemas.py exactly (Phase E's
 * POST /api/analyze response). Field names are kept snake_case,
 * matching the wire JSON verbatim -- a deliberate choice to avoid a
 * separate mapping layer that could silently drift from the actual API
 * contract. See docs/api.md for the authoritative schema.
 */

export type EssayState =
  | "machine_signal_detected"
  | "no_strong_signal_detected"
  | "inconclusive";

export interface EvidenceItem {
  feature: string;
  human_label: string;
  observed_value: number;
  reference_mean: number;
  reference_std: number;
  direction: "higher" | "lower";
  contribution: number;
  statement: string;
}

export interface EssayResult {
  state: EssayState;
  score: number | null;
  state_explanation: string;
  evidence: EvidenceItem[];
  limitation_note: string;
}

export interface SentenceCandidate {
  sentence_index: number;
  rank: number;
  text: string;
  char_start: number;
  char_end: number;
  score: number;
  label: string; // always "potentially_ai_assisted" per the backend contract
  evidence: EvidenceItem[];
}

export interface SkippedSentence {
  sentence_index: number;
  text: string;
  char_start: number;
  char_end: number;
  reason: string;
}

export interface SentenceResult {
  candidates: SentenceCandidate[];
  skipped: SkippedSentence[];
  top_k: number;
  total_scorable_sentences: number;
  has_evidence: boolean;
  no_evidence_reason: string | null;
  disclaimer: string;
}

export interface AnalysisMetadata {
  essay_model_version: string;
  essay_source_experiment: string;
  sentence_model_version: string;
  sentence_source_experiment: string;
}

export interface AnalyzeResponse {
  analysis_id: string;
  normalized_text: string;
  essay: EssayResult;
  sentences: SentenceResult;
  metadata: AnalysisMetadata;
}
