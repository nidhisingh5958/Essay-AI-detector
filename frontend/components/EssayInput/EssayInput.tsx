"use client";

import type { AnalysisStatus } from "@/lib/useEssayAnalysis";

const MAX_CHARS = 20000; // matches backend/app/config.py's max_essay_chars exactly (Phase E's 413 boundary)

interface EssayInputProps {
  text: string;
  onTextChange: (text: string) => void;
  onAnalyze: () => void;
  status: AnalysisStatus;
  canAnalyze: boolean;
}

/**
 * Purely presentational + local-state-free: all analysis state lives in
 * useEssayAnalysis (Phase F item 20 -- centralized state, not scattered
 * booleans). Contains no detection logic, no score/threshold
 * calculation, no feature extraction -- calling onAnalyze is the only
 * thing this component does when the user acts.
 */
export function EssayInput({ text, onTextChange, onAnalyze, status, canAnalyze }: EssayInputProps) {
  const isAnalyzing = status === "analyzing";

  return (
    <div className="flex w-full flex-col gap-4">
      <label htmlFor="essay-text" className="sr-only">
        Essay text to analyze
      </label>
      <textarea
        id="essay-text"
        className="min-h-[280px] w-full resize-y rounded-md border border-zinc-300 bg-white p-4 font-serif text-base leading-relaxed text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        placeholder="Paste an admissions essay to analyze..."
        value={text}
        onChange={(e) => onTextChange(e.target.value)}
        maxLength={MAX_CHARS}
        disabled={isAnalyzing}
        aria-describedby="essay-char-count"
      />
      <div className="flex items-center justify-between text-sm text-zinc-500 dark:text-zinc-400">
        <span id="essay-char-count">
          {text.length} / {MAX_CHARS} characters
        </span>
        <button
          type="button"
          onClick={onAnalyze}
          disabled={!canAnalyze}
          className="rounded-md bg-zinc-900 px-5 py-2 font-medium text-white transition-colors hover:bg-zinc-700 focus:outline-none focus:ring-2 focus:ring-zinc-400 disabled:cursor-not-allowed disabled:bg-zinc-300 disabled:text-zinc-600 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-500"
        >
          {isAnalyzing ? "Analyzing…" : "Analyze"}
        </button>
      </div>
    </div>
  );
}
