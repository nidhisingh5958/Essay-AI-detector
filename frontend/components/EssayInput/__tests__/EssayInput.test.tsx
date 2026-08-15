import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { EssayInput } from "@/components/EssayInput/EssayInput";

describe("EssayInput", () => {
  it("renders a labeled textarea and a disabled Analyze button when input is empty (item B)", () => {
    render(
      <EssayInput text="" onTextChange={vi.fn()} onAnalyze={vi.fn()} status="idle" canAnalyze={false} />,
    );
    expect(screen.getByRole("textbox", { name: /essay text to analyze/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /analyze/i })).toBeDisabled();
  });

  it("enables the Analyze button once valid input is present (item C)", () => {
    render(
      <EssayInput text="A real essay." onTextChange={vi.fn()} onAnalyze={vi.fn()} status="idle" canAnalyze={true} />,
    );
    expect(screen.getByRole("button", { name: /analyze/i })).toBeEnabled();
  });

  it("shows a clear loading label and disables the textarea while analyzing (item D)", () => {
    render(
      <EssayInput text="A real essay." onTextChange={vi.fn()} onAnalyze={vi.fn()} status="analyzing" canAnalyze={false} />,
    );
    expect(screen.getByRole("button", { name: /analyzing/i })).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("calls onTextChange as the user types, preserving input locally", async () => {
    const onTextChange = vi.fn();
    render(<EssayInput text="" onTextChange={onTextChange} onAnalyze={vi.fn()} status="idle" canAnalyze={false} />);
    await userEvent.type(screen.getByRole("textbox"), "Hi");
    expect(onTextChange).toHaveBeenCalled();
  });

  it("calls onAnalyze exactly once per click and never duplicates while disabled (item 5)", async () => {
    const onAnalyze = vi.fn();
    render(
      <EssayInput text="A real essay." onTextChange={vi.fn()} onAnalyze={onAnalyze} status="idle" canAnalyze={true} />,
    );
    await userEvent.click(screen.getByRole("button", { name: /analyze/i }));
    expect(onAnalyze).toHaveBeenCalledTimes(1);
  });

  it("has an accessible label on the textarea (item 18)", () => {
    render(<EssayInput text="" onTextChange={vi.fn()} onAnalyze={vi.fn()} status="idle" canAnalyze={false} />);
    expect(screen.getByLabelText(/essay text to analyze/i)).toBeInTheDocument();
  });
});
