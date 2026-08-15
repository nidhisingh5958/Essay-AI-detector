import type { EvidenceItem } from "@/types/api";

interface EvidencePanelProps {
  evidence: EvidenceItem[];
  emptyMessage?: string;
}

/**
 * Renders the backend's already-composed evidence statements verbatim
 * -- this component is presentation only (Phase F item 9). It never
 * displays a raw internal feature name (e.g. `stylo_type_token_ratio`);
 * only `human_label` and the fixed `statement` the evidence mapper
 * (DEC-017) already produced.
 */
export function EvidencePanel({ evidence, emptyMessage }: EvidencePanelProps) {
  if (evidence.length === 0) {
    return emptyMessage ? (
      <p className="text-sm text-zinc-500 dark:text-zinc-400">{emptyMessage}</p>
    ) : null;
  }

  return (
    <ul className="flex flex-col gap-2">
      {evidence.map((item) => (
        <li
          key={item.feature}
          className="rounded-md border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300"
        >
          <span className="mb-1 block font-medium text-zinc-900 dark:text-zinc-100">
            {item.human_label}
          </span>
          <span>{item.statement}</span>
        </li>
      ))}
    </ul>
  );
}
