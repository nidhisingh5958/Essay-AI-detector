"use client";

import { EssayInput } from "@/components/EssayInput/EssayInput";
import { EssayViewer } from "@/components/EssayViewer/EssayViewer";
import { Limitations } from "@/components/Limitations/Limitations";
import { ResultsSummary } from "@/components/ResultsSummary/ResultsSummary";
import { StatusMessage } from "@/components/StatusMessage/StatusMessage";
import { useEssayAnalysis } from "@/lib/useEssayAnalysis";

export default function Home() {
  const analysis = useEssayAnalysis();

  return (
    <div className="flex flex-1 justify-center bg-zinc-50 dark:bg-black">
      <main className="flex w-full max-w-3xl flex-col gap-6 px-6 py-16">
        <header className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            AI Detector for Admissions Essays
          </h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            Paste an essay to see measurable, sentence-level evidence about its writing
            characteristics. This tool reports statistical patterns — it does not establish
            authorship with certainty.
          </p>
        </header>

        <EssayInput
          text={analysis.text}
          onTextChange={analysis.setText}
          onAnalyze={analysis.analyze}
          status={analysis.status}
          canAnalyze={analysis.canAnalyze}
        />

        {analysis.status === "analyzing" && (
          <StatusMessage variant="loading" message="Analyzing essay…" />
        )}

        {analysis.status === "error" && analysis.error && (
          <StatusMessage variant="error" message={analysis.error} />
        )}

        {analysis.status === "success" && analysis.result && (
          <div className="flex flex-col gap-8">
            <ResultsSummary essay={analysis.result.essay} />
            <EssayViewer
              normalizedText={analysis.result.normalized_text}
              sentences={analysis.result.sentences}
            />
            <Limitations limitationNote={analysis.result.essay.limitation_note} />
          </div>
        )}
      </main>
    </div>
  );
}
