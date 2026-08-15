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

  const isNearLimit = text.length > MAX_CHARS * 0.9;

  return (
    <div className="panel flex w-full flex-col gap-3 p-4 sm:p-5">
      <label htmlFor="essay-text" className="sr-only">
        Essay text to analyze
      </label>
      <textarea
        id="essay-text"
        className="min-h-[280px] w-full resize-y rounded-lg border border-zinc-200 bg-zinc-50 p-4 font-serif text-base leading-relaxed text-zinc-900 transition-colors placeholder:text-zinc-400 focus:border-accent focus:bg-white focus:outline-none focus:ring-2 focus:ring-accent/40 disabled:opacity-60 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-50 dark:placeholder:text-zinc-600 dark:focus:bg-zinc-950"
        placeholder="Paste an admissions essay to analyze..."
        value={text}
        onChange={(e) => onTextChange(e.target.value)}
        maxLength={MAX_CHARS}
        disabled={isAnalyzing}
        aria-describedby="essay-char-count"
      />
      <div className="flex items-center justify-between gap-3">
        <span
          id="essay-char-count"
          className={`text-sm ${isNearLimit ? "text-amber-600 dark:text-amber-400" : "text-zinc-500 dark:text-zinc-400"}`}
        >
          {text.length.toLocaleString()} / {MAX_CHARS.toLocaleString()} characters
        </span>
        <button
          type="button"
          onClick={onAnalyze}
          disabled={!canAnalyze}
          className="flex items-center gap-2 rounded-lg bg-accent px-5 py-2 font-medium text-accent-foreground shadow-sm transition-colors hover:bg-accent/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-white disabled:cursor-not-allowed disabled:bg-zinc-200 disabled:text-zinc-500 disabled:shadow-none dark:focus-visible:ring-offset-zinc-900 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-500"
        >
          {isAnalyzing && (
            <svg viewBox="0 0 24 24" fill="none" className="size-4 animate-spin" aria-hidden="true">
              <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" className="opacity-25" />
              <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" className="opacity-90" />
            </svg>
          )}
          {isAnalyzing ? "Analyzing…" : "Analyze"}
        </button>
      </div>
    </div>
  );
}
