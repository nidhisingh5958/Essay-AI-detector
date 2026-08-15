import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as apiModule from "@/lib/api";
import { useEssayAnalysis } from "@/lib/useEssayAnalysis";
import sampleResponse from "@/lib/__fixtures__/sampleAnalyzeResponse.json";
import type { AnalyzeResponse } from "@/types/api";

describe("useEssayAnalysis", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("starts in the idle state with empty text", () => {
    const { result } = renderHook(() => useEssayAnalysis());
    expect(result.current.status).toBe("idle");
    expect(result.current.text).toBe("");
    expect(result.current.canAnalyze).toBe(false);
  });

  it("canAnalyze becomes true once non-whitespace text is entered", () => {
    const { result } = renderHook(() => useEssayAnalysis());
    act(() => result.current.setText("   "));
    expect(result.current.canAnalyze).toBe(false);
    act(() => result.current.setText("real text"));
    expect(result.current.canAnalyze).toBe(true);
  });

  it("moves to the error state without calling the API for empty text", async () => {
    const spy = vi.spyOn(apiModule, "analyzeEssay");
    const { result } = renderHook(() => useEssayAnalysis());

    await act(async () => {
      await result.current.analyze();
    });

    expect(result.current.status).toBe("error");
    expect(result.current.error).toMatch(/enter some essay text/i);
    expect(spy).not.toHaveBeenCalled();
  });

  it("transitions idle -> analyzing -> success on a successful API call", async () => {
    vi.spyOn(apiModule, "analyzeEssay").mockResolvedValue(sampleResponse as AnalyzeResponse);
    const { result } = renderHook(() => useEssayAnalysis());
    act(() => result.current.setText("a real essay"));

    const promise = act(async () => {
      await result.current.analyze();
    });
    await promise;

    await waitFor(() => expect(result.current.status).toBe("success"));
    expect(result.current.result?.analysis_id).toBe(sampleResponse.analysis_id);
  });

  it("transitions to the error state on API failure, without a stale result", async () => {
    vi.spyOn(apiModule, "analyzeEssay").mockRejectedValue(new apiModule.ApiError("Service unavailable.", 503));
    const { result } = renderHook(() => useEssayAnalysis());
    act(() => result.current.setText("a real essay"));

    await act(async () => {
      await result.current.analyze();
    });

    expect(result.current.status).toBe("error");
    expect(result.current.error).toBe("Service unavailable.");
    expect(result.current.result).toBeNull();
  });

  it("repeated analyze() calls with the same text produce consistent, non-stale results", async () => {
    vi.spyOn(apiModule, "analyzeEssay").mockResolvedValue(sampleResponse as AnalyzeResponse);
    const { result } = renderHook(() => useEssayAnalysis());
    act(() => result.current.setText("a real essay"));

    await act(async () => {
      await result.current.analyze();
    });
    await act(async () => {
      await result.current.analyze();
    });

    expect(result.current.status).toBe("success");
    expect(result.current.result?.essay.state).toBe(sampleResponse.essay.state);
  });
});
