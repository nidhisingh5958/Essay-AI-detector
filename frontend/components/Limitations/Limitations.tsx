interface LimitationsProps {
  limitationNote: string;
}

/**
 * The fixed, always-visible honesty section (Phase F item 14). The
 * per-analysis `limitationNote` comes from the backend (DEC-017's
 * evidence mapper); the general points below are static product-level
 * scope statements, not experimental statistics -- no accuracy/recall/
 * precision number appears anywhere in this component (item 25).
 */
export function Limitations({ limitationNote }: LimitationsProps) {
  return (
    <section
      aria-labelledby="limitations-heading"
      className="panel flex flex-col gap-2 p-4 text-sm text-zinc-700 sm:p-5 dark:text-zinc-300"
    >
      <h2 id="limitations-heading" className="font-semibold text-zinc-900 dark:text-zinc-100">
        Limitations
      </h2>
      <p>{limitationNote}</p>
      <ul className="list-disc space-y-1 pl-5">
        <li>The detector identifies statistical patterns in writing. It does not prove authorship.</li>
        <li>
          Whole-essay AI-generation detection was evaluated against this project&apos;s reference data
          and two tested AI writing models — it is not a claim of universal AI detection.
        </li>
        <li>Lightly AI-assisted writing (e.g. editing help) is substantially harder to identify reliably.</li>
        <li>Highlighted passages are candidates for review, not proof that AI wrote them.</li>
      </ul>
    </section>
  );
}
