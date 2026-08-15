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
      className={`rounded-md border px-4 py-3 text-sm ${
        isError
          ? "border-red-300 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
          : "border-zinc-300 bg-zinc-50 text-zinc-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
      }`}
    >
      {message}
    </div>
  );
}
