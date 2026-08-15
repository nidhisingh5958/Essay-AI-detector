import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, analyzeEssay } from "@/lib/api";
import sampleResponse from "@/lib/__fixtures__/sampleAnalyzeResponse.json";

describe("analyzeEssay", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the parsed response on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => sampleResponse,
      }),
    );

    const result = await analyzeEssay("some essay text");
    expect(result.analysis_id).toBe(sampleResponse.analysis_id);
    expect(result.essay.state).toBe(sampleResponse.essay.state);
  });

  it("sends the essay text as the request body", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => sampleResponse });
    vi.stubGlobal("fetch", fetchMock);

    await analyzeEssay("my essay");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, init] = fetchMock.mock.calls[0];
    expect(JSON.parse(init.body)).toEqual({ text: "my essay" });
  });

  it("throws ApiError with the backend's detail message on a 4xx/5xx response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: async () => ({ detail: "Essay text is empty." }),
      }),
    );

    await expect(analyzeEssay("")).rejects.toThrow("Essay text is empty.");
  });

  it("falls back to a generic message if the error body is not valid JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error("not json");
        },
      }),
    );

    await expect(analyzeEssay("x")).rejects.toThrow(ApiError);
  });

  it("throws a network-failure ApiError if fetch itself rejects", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );

    await expect(analyzeEssay("x")).rejects.toThrow(/reach the analysis service/i);
  });

  it("never leaks a raw stack trace or filesystem path from an error body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ detail: "An unexpected error occurred while analyzing this essay." }),
      }),
    );

    try {
      await analyzeEssay("x");
      throw new Error("expected analyzeEssay to throw");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      const message = (err as ApiError).message;
      expect(message).not.toMatch(/\/Users\/|\/Volumes\/|Traceback/);
    }
  });
});
