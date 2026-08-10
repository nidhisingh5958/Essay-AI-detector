"use client";

import { useState } from "react";

/**
 * Phase 1 scaffold: captures essay text and reserves the interaction shape
 * (paste -> analyze) that later phases wire to POST /api/analyze.
 * Intentionally has no analysis logic yet — see docs/project-status.md.
 */
export function EssayInput() {
  const [text, setText] = useState("");

  return (
    <div className="flex w-full flex-col gap-4">
      <textarea
        className="min-h-[280px] w-full resize-y rounded-md border border-zinc-300 bg-white p-4 font-serif text-base leading-relaxed text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        placeholder="Paste an admissions essay to analyze..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        maxLength={20000}
      />
      <div className="flex items-center justify-between text-sm text-zinc-500 dark:text-zinc-400">
        <span>{text.length} / 20000 characters</span>
        <button
          type="button"
          disabled
          title="Analysis pipeline is not implemented yet (see docs/project-status.md)"
          className="cursor-not-allowed rounded-md bg-zinc-300 px-5 py-2 font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-500"
        >
          Analyze (coming in a later phase)
        </button>
      </div>
    </div>
  );
}
