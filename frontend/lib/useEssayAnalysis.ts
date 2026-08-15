"use client";

import { useCallback, useState } from "react";

import { ApiError, analyzeEssay } from "@/lib/api";
import type { AnalyzeResponse } from "@/types/api";

/**
 * Explicit state model (Phase F item 20) -- one discriminated status
 * field, not a tangle of independent booleans:
 *   idle        -- nothing submitted yet
 *   validating  -- checking the input is non-empty before calling the API
 *   analyzing   -- request in flight
 *   success     -- result is available
 *   error       -- either client-side validation or an API failure
 */
export type AnalysisStatus = "idle" | "validating" | "analyzing" | "success" | "error";

export interface EssayAnalysisState {
  text: string;
  setText: (text: string) => void;
  status: AnalysisStatus;
  result: AnalyzeResponse | null;
  error: string | null;
  canAnalyze: boolean;
  analyze: () => Promise<void>;
}

export function useEssayAnalysis(): EssayAnalysisState {
  const [text, setText] = useState("");
  const [status, setStatus] = useState<AnalysisStatus>("idle");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canAnalyze = text.trim().length > 0 && status !== "analyzing";

  const analyze = useCallback(async () => {
    setStatus("validating");

    if (text.trim().length === 0) {
      setError("Please enter some essay text to analyze.");
      setStatus("error");
      return;
    }

    setStatus("analyzing");
    setError(null);

    try {
      const response = await analyzeEssay(text);
      setResult(response);
      setStatus("success");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong while analyzing this essay.");
      setStatus("error");
    }
  }, [text]);

  return { text, setText, status, result, error, canAnalyze, analyze };
}
