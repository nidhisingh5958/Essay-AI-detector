"use client";

import { useState } from "react";

import { EvidencePanel } from "@/components/EvidencePanel/EvidencePanel";
import { buildHighlightSegments } from "@/lib/textOffsets";
import type { SentenceCandidate, SentenceResult } from "@/types/api";

interface EssayViewerProps {
  normalizedText: string;
  sentences: SentenceResult;
}

/**
 * Renders `normalizedText` with the backend's ranked candidate passages
 * highlighted. Offsets are used EXACTLY as returned -- no re-tokenizing,
 * no recomputing sentence boundaries in JavaScript (Phase F item 10).
 * `buildHighlightSegments` (lib/textOffsets.ts) is the only thing that
 * slices the text, and it slices by Unicode code point to stay correct
 * for any input (see that module's docstring for why plain `.slice()`
 * would be wrong).
 */
export function EssayViewer({ normalizedText, sentences }: EssayViewerProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!sentences.has_evidence) {
    return (
      <section className="panel flex flex-col gap-2 p-4 sm:p-5">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Potentially AI-assisted passages
        </h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          {sentences.no_evidence_reason
            ? `No candidate passages could be evaluated: ${sentences.no_evidence_reason}.`
            : "No candidate passages could be evaluated for this essay."}
        </p>
      </section>
    );
  }

  const segments = buildHighlightSegments(normalizedText, sentences.candidates);

  return (
    <section className="panel flex flex-col gap-4 p-4 sm:p-5">
      <div className="flex flex-col gap-1">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Potentially AI-assisted passages
        </h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">{sentences.disclaimer}</p>
      </div>

      <p className="whitespace-pre-wrap rounded-lg border border-zinc-200 bg-zinc-50 p-4 font-serif text-base leading-relaxed text-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-50">
        {segments.map((segment, i) =>
          segment.candidate ? (
            <mark
              key={i}
              tabIndex={0}
              role="button"
              aria-expanded={expandedIndex === segment.candidate.sentence_index}
              aria-label={`Potentially AI-assisted passage, rank ${segment.candidate.rank}. Activate to view evidence.`}
              onClick={() =>
                setExpandedIndex((current) =>
                  current === segment.candidate!.sentence_index ? null : segment.candidate!.sentence_index,
                )
              }
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setExpandedIndex((current) =>
                    current === segment.candidate!.sentence_index ? null : segment.candidate!.sentence_index,
                  );
                }
              }}
              className="cursor-pointer rounded bg-amber-200 px-0.5 underline decoration-amber-500 decoration-2 underline-offset-2 transition-colors hover:bg-amber-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 dark:bg-amber-900 dark:text-amber-100 dark:hover:bg-amber-800"
              title={`Rank ${segment.candidate.rank} — potentially AI-assisted passage`}
            >
              {segment.text}
            </mark>
          ) : (
            <span key={i}>{segment.text}</span>
          ),
        )}
      </p>

      <ul className="flex flex-col gap-2">
        {sentences.candidates.map((candidate) => (
          <CandidateDetail
            key={candidate.sentence_index}
            candidate={candidate}
            expanded={expandedIndex === candidate.sentence_index}
            onToggle={() =>
              setExpandedIndex((current) => (current === candidate.sentence_index ? null : candidate.sentence_index))
            }
          />
        ))}
      </ul>

      {sentences.skipped.length > 0 && (
        <p className="text-xs text-zinc-500 dark:text-zinc-500">
          Some passages could not be scored and are not shown above ({sentences.skipped.length} sentence
          {sentences.skipped.length === 1 ? "" : "s"} skipped).
        </p>
      )}
    </section>
  );
}

interface CandidateDetailProps {
  candidate: SentenceCandidate;
  expanded: boolean;
  onToggle: () => void;
}

function CandidateDetail({ candidate, expanded, onToggle }: CandidateDetailProps) {
  return (
    <li className="overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={expanded}
        className="flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left text-sm font-medium text-zinc-900 transition-colors hover:bg-zinc-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent dark:text-zinc-100 dark:hover:bg-zinc-900"
      >
        <span className="flex items-center gap-2">
          <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-amber-100 text-xs font-semibold text-amber-800 dark:bg-amber-900 dark:text-amber-200">
            {candidate.rank}
          </span>
          Potentially AI-assisted passage
        </span>
        <span
          aria-hidden="true"
          className={`text-zinc-400 transition-transform ${expanded ? "rotate-45" : ""}`}
        >
          +
        </span>
      </button>
      {expanded && (
        <div className="border-t border-zinc-200 bg-zinc-50/60 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950/60">
          <EvidencePanel evidence={candidate.evidence} emptyMessage="No specific evidence was available for this passage." />
        </div>
      )}
    </li>
  );
}
