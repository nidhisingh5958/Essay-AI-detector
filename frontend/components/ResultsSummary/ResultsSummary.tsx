import { EvidencePanel } from "@/components/EvidencePanel/EvidencePanel";
import type { EssayResult, EssayState } from "@/types/api";

/**
 * State labels/icons (Phase F item 7/8/18): the state is always shown
 * as TEXT, never conveyed by color alone -- the icon glyph and label
 * are the primary signal; background color is a secondary reinforcement
 * only. No wording here implies certainty ("detected" describes a
 * measured signal, not a proven fact) and no raw percentage is ever
 * rendered as "XX% AI".
 */
const STATE_CONFIG: Record<
  EssayState,
  { label: string; icon: string; badgeClass: string }
> = {
  machine_signal_detected: {
    label: "Machine-generated signal detected",
    icon: "⚠",
    badgeClass:
      "border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200",
  },
  no_strong_signal_detected: {
    label: "No strong machine-generated signal detected",
    icon: "✓",
    badgeClass:
      "border-emerald-300 bg-emerald-50 text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-200",
  },
  inconclusive: {
    label: "Inconclusive",
    icon: "?",
    badgeClass:
      "border-zinc-300 bg-zinc-100 text-zinc-800 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200",
  },
};

interface ResultsSummaryProps {
  essay: EssayResult;
}

export function ResultsSummary({ essay }: ResultsSummaryProps) {
  const config = STATE_CONFIG[essay.state];

  return (
    <section className="flex flex-col gap-4" aria-labelledby="essay-result-heading">
      <div className={`flex items-center gap-3 rounded-md border px-4 py-3 ${config.badgeClass}`}>
        <span aria-hidden="true" className="text-lg">
          {config.icon}
        </span>
        <h2 id="essay-result-heading" className="font-semibold">
          {config.label}
        </h2>
      </div>

      <p className="text-sm text-zinc-700 dark:text-zinc-300">{essay.state_explanation}</p>

      {essay.score !== null && (
        <p className="text-xs text-zinc-500 dark:text-zinc-500">
          Detector score: {essay.score.toFixed(2)} (0–1 scale; a measure of similarity to the
          machine-generated reference data used to build this detector — not a probability that AI
          wrote this essay).
        </p>
      )}

      {essay.evidence.length > 0 && (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
            What the detector measured
          </h3>
          <EvidencePanel evidence={essay.evidence} />
        </div>
      )}
    </section>
  );
}
