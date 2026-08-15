interface StatusMessageProps {
  variant: "loading" | "error";
  message: string;
}

/**
 * Small, single-purpose banner for the "analyzing" and "error" states
 * (Phase F item 16/15). Loading copy deliberately avoids implying the
 * system is "thinking" like a generative model -- it is running a
 * fixed feature-extraction + scoring pipeline.
 */
export function StatusMessage({ variant, message }: StatusMessageProps) {
  const isError = variant === "error";
  return (
    <div
      role={isError ? "alert" : "status"}
      aria-live={isError ? "assertive" : "polite"}
      className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-sm ${
        isError
          ? "border-red-300 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
          : "border-zinc-200 bg-white text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300"
      }`}
    >
      {isError ? (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="size-4 shrink-0" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.29 3.86 1.82 18a1 1 0 0 0 .86 1.5h18.64a1 1 0 0 0 .86-1.5L13.71 3.86a1 1 0 0 0-1.72 0Z" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" fill="none" className="size-4 shrink-0 animate-spin text-accent" aria-hidden="true">
          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" className="opacity-25" />
          <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" className="opacity-90" />
        </svg>
      )}
      {message}
    </div>
  );
}
