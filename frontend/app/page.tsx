import { EssayInput } from "@/components/EssayInput/EssayInput";

export default function Home() {
  return (
    <div className="flex flex-1 justify-center bg-zinc-50 dark:bg-black">
      <main className="flex w-full max-w-3xl flex-col gap-6 px-6 py-16">
        <header className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            AI Detector for Admissions Essays
          </h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            Paste an essay to inspect measurable, sentence-level evidence about
            its writing characteristics. This tool estimates writing
            characteristics — it does not establish authorship.
          </p>
        </header>

        <EssayInput />

        <p className="text-xs text-zinc-500 dark:text-zinc-500">
          Project status: repository scaffold (Phase 1). Analysis is not yet
          implemented — see{" "}
          <code className="font-mono">docs/project-status.md</code> in the
          repository for current progress.
        </p>
      </main>
    </div>
  );
}
