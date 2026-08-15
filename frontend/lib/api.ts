/**
 * Typed client for the production analysis API (Phase E: POST
 * /api/analyze). This is the ONLY place the frontend talks to the
 * backend -- no other module should call fetch() against the analysis
 * endpoint, and no other module should compute a score, threshold, or
 * feature value. The API base URL is configurable (never hardcoded),
 * see docs/frontend.md "Local development" for how to set it.
 */

import type { AnalyzeResponse } from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function analyzeEssay(text: string): Promise<AnalyzeResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
  } catch {
    // Network failure (backend unreachable) -- never surfaced as a
    // successful/empty analysis.
    throw new ApiError(
      "Could not reach the analysis service. Please check your connection and try again.",
      0,
    );
  }

  if (!response.ok) {
    let detail = "The analysis service returned an error.";
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Response body wasn't JSON (or was empty) -- keep the generic
      // message. Never surface raw response text, which could contain
      // an HTML error page or a stack trace from an intermediary proxy.
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as AnalyzeResponse;
}
