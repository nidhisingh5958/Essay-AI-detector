import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { EssayViewer } from "@/components/EssayViewer/EssayViewer";
import sampleResponse from "@/lib/__fixtures__/sampleAnalyzeResponse.json";
import unicodeResponse from "@/lib/__fixtures__/unicodeAnalyzeResponse.json";
import type { AnalyzeResponse } from "@/types/api";

const sample = sampleResponse as AnalyzeResponse;
const unicode = unicodeResponse as AnalyzeResponse;

describe("EssayViewer", () => {
  it("renders every candidate's own text as a highlighted mark (item J/K)", () => {
    const { container } = render(
      <EssayViewer normalizedText={sample.normalized_text} sentences={sample.sentences} />,
    );
    const marks = container.querySelectorAll("mark");
    expect(marks).toHaveLength(sample.sentences.candidates.length);
    for (const candidate of sample.sentences.candidates) {
      expect(screen.getByText(candidate.text)).toBeInTheDocument();
    }
  });

  it("uses the cautious label, never an authorship-certainty claim (item 11/G)", () => {
    render(<EssayViewer normalizedText={sample.normalized_text} sentences={sample.sentences} />);
    const body = document.body.textContent ?? "";
    expect(body).toMatch(/potentially ai-assisted/i);
    expect(body).not.toMatch(/ai-written sentence/i);
    expect(body).not.toMatch(/ai-generated sentence/i);
    expect(body).not.toMatch(/definitely ai/i);
  });

  it("shows the disclaimer text returned by the API verbatim", () => {
    render(<EssayViewer normalizedText={sample.normalized_text} sentences={sample.sentences} />);
    expect(screen.getByText(sample.sentences.disclaimer)).toBeInTheDocument();
  });

  it("reports skipped sentences without hiding that some text could not be scored (item L/13)", () => {
    render(<EssayViewer normalizedText={sample.normalized_text} sentences={sample.sentences} />);
    expect(sample.sentences.skipped.length).toBeGreaterThan(0);
    expect(screen.getByText(/could not be scored/i)).toBeInTheDocument();
  });

  it("expands a candidate's evidence on click (item 12)", async () => {
    render(<EssayViewer normalizedText={sample.normalized_text} sentences={sample.sentences} />);
    const toggle = screen.getAllByRole("button", { name: /potentially ai-assisted passage/i })[0];
    await userEvent.click(toggle);
    const firstCandidate = sample.sentences.candidates[0];
    if (firstCandidate.evidence.length > 0) {
      expect(screen.getByText(firstCandidate.evidence[0].statement)).toBeInTheDocument();
    }
  });

  it("shows an explicit no-evidence state rather than an empty screen (item M/F)", () => {
    render(
      <EssayViewer
        normalizedText="Some text."
        sentences={{
          candidates: [],
          skipped: [],
          top_k: 3,
          total_scorable_sentences: 0,
          has_evidence: false,
          no_evidence_reason: "no scorable sentences (no sentences with sufficient language-model-scorable content)",
          disclaimer: "disclaimer text",
        }}
      />,
    );
    expect(screen.getByText(/no candidate passages could be evaluated/i)).toBeInTheDocument();
  });

  it("handles Unicode text (including emoji) without breaking the highlight mapping (item O)", () => {
    render(<EssayViewer normalizedText={unicode.normalized_text} sentences={unicode.sentences} />);
    for (const candidate of unicode.sentences.candidates) {
      expect(screen.getByText(candidate.text)).toBeInTheDocument();
    }
  });
});
