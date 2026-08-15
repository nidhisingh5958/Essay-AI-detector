import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ResultsSummary } from "@/components/ResultsSummary/ResultsSummary";
import type { EssayResult } from "@/types/api";

const baseEssay: EssayResult = {
  state: "machine_signal_detected",
  score: 0.73,
  state_explanation: "This score reflects the detector's learned distinction...",
  evidence: [
    {
      feature: "stylo_type_token_ratio",
      human_label: "vocabulary diversity",
      observed_value: 0.9,
      reference_mean: 0.46,
      reference_std: 0.07,
      direction: "higher",
      contribution: 0.4,
      statement: "This shows a higher level of vocabulary diversity than the reference range used by the detector.",
    },
  ],
  limitation_note: "This result is scoped to full-essay AI generation...",
};

describe("ResultsSummary", () => {
  it("renders the machine_signal_detected state as text (item F/7)", () => {
    render(<ResultsSummary essay={baseEssay} />);
    expect(screen.getByText(/machine-generated signal detected/i)).toBeInTheDocument();
  });

  it("renders the no_strong_signal_detected state as text (item G)", () => {
    render(<ResultsSummary essay={{ ...baseEssay, state: "no_strong_signal_detected", score: 0.1 }} />);
    expect(screen.getByText(/no strong machine-generated signal detected/i)).toBeInTheDocument();
  });

  it("renders the inconclusive state as text, with no score shown (item H)", () => {
    render(<ResultsSummary essay={{ ...baseEssay, state: "inconclusive", score: null, evidence: [] }} />);
    expect(screen.getByText(/inconclusive/i)).toBeInTheDocument();
    expect(screen.queryByText(/detector score/i)).not.toBeInTheDocument();
  });

  it("never displays a raw '% AI' or 'AI probability' claim (item 7/25)", () => {
    render(<ResultsSummary essay={baseEssay} />);
    const body = document.body.textContent ?? "";
    expect(body).not.toMatch(/\d+%\s*AI/i);
    expect(body).not.toMatch(/AI probability/i);
    expect(body).not.toMatch(/73%/); // the raw score must never be rendered as a bare percentage
  });

  it("labels the raw score explicitly as a detector score, not an authorship probability, when shown", () => {
    render(<ResultsSummary essay={baseEssay} />);
    expect(screen.getByText(/detector score/i)).toBeInTheDocument();
    expect(screen.getByText(/not a probability that ai wrote this essay/i)).toBeInTheDocument();
  });

  it("renders evidence via EvidencePanel (item I)", () => {
    render(<ResultsSummary essay={baseEssay} />);
    expect(screen.getAllByText(/vocabulary diversity/i).length).toBeGreaterThan(0);
    expect(screen.getByText(baseEssay.evidence[0].statement)).toBeInTheDocument();
  });

  it("does not display any research performance statistic as per-input confidence (item 25)", () => {
    render(<ResultsSummary essay={baseEssay} />);
    const body = document.body.textContent ?? "";
    expect(body).not.toMatch(/97\.8%/);
    expect(body).not.toMatch(/86\.7%/);
    expect(body).not.toMatch(/17\.6%/);
  });
});
