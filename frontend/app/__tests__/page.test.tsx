import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import Home from "@/app/page";
import * as apiModule from "@/lib/api";
import sampleResponse from "@/lib/__fixtures__/sampleAnalyzeResponse.json";
import type { AnalyzeResponse } from "@/types/api";

describe("Home page — end-to-end integration", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the initial landing state with a disabled Analyze button (item A)", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: /ai detector for admissions essays/i })).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /analyze/i })).toBeDisabled();
  });

  it("runs the full flow: type essay -> analyze -> see results (items E/I/J)", async () => {
    vi.spyOn(apiModule, "analyzeEssay").mockResolvedValue(sampleResponse as AnalyzeResponse);
    render(<Home />);

    await userEvent.type(screen.getByRole("textbox"), "A representative admissions essay.");
    await userEvent.click(screen.getByRole("button", { name: /analyze/i }));

    await waitFor(() =>
      expect(screen.getByText(/machine-generated signal detected/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/potentially ai-assisted passages/i)).toBeInTheDocument();
    expect(screen.getByText(/limitations/i)).toBeInTheDocument();
  });

  it("shows a clear loading state while the request is in flight (item D)", async () => {
    let resolvePromise: (value: AnalyzeResponse) => void = () => {};
    vi.spyOn(apiModule, "analyzeEssay").mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve;
      }),
    );
    render(<Home />);

    await userEvent.type(screen.getByRole("textbox"), "A real essay here.");
    await userEvent.click(screen.getByRole("button", { name: /analyze/i }));

    expect(screen.getByText(/analyzing essay/i)).toBeInTheDocument();
    resolvePromise(sampleResponse as AnalyzeResponse);
    await waitFor(() => expect(screen.queryByText(/analyzing essay/i)).not.toBeInTheDocument());
  });

  it("shows a clear, non-leaking error state on API failure (item M)", async () => {
    vi.spyOn(apiModule, "analyzeEssay").mockRejectedValue(
      new apiModule.ApiError("The analysis service returned an error.", 500),
    );
    render(<Home />);

    await userEvent.type(screen.getByRole("textbox"), "A real essay here.");
    await userEvent.click(screen.getByRole("button", { name: /analyze/i }));

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByRole("alert").textContent).not.toMatch(/\/Users\/|\/Volumes\/|Traceback/);
  });

  it("supports repeated analysis after editing the essay (item N)", async () => {
    const spy = vi
      .spyOn(apiModule, "analyzeEssay")
      .mockResolvedValueOnce(sampleResponse as AnalyzeResponse)
      .mockResolvedValueOnce({
        ...(sampleResponse as AnalyzeResponse),
        essay: { ...(sampleResponse as AnalyzeResponse).essay, state: "no_strong_signal_detected", score: 0.1 },
      });
    render(<Home />);

    const textarea = screen.getByRole("textbox");
    await userEvent.type(textarea, "First essay version.");
    await userEvent.click(screen.getByRole("button", { name: /analyze/i }));
    await waitFor(() => expect(screen.getByText(/machine-generated signal detected/i)).toBeInTheDocument());

    await userEvent.clear(textarea);
    await userEvent.type(textarea, "A completely different essay version.");
    await userEvent.click(screen.getByRole("button", { name: /analyze/i }));
    await waitFor(() =>
      expect(screen.getByText(/no strong machine-generated signal detected/i)).toBeInTheDocument(),
    );

    expect(spy).toHaveBeenCalledTimes(2);
  });

  it("primary controls are keyboard-accessible with visible labels (item P/18)", () => {
    render(<Home />);
    const textarea = screen.getByLabelText(/essay text to analyze/i);
    expect(textarea).toBeInTheDocument();
    expect(textarea.tagName.toLowerCase()).toBe("textarea");

    const button = screen.getByRole("button", { name: /analyze/i });
    expect(button.tagName.toLowerCase()).toBe("button"); // a real, semantic, keyboard-focusable button
  });
});
