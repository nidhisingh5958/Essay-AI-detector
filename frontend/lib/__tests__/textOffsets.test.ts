import { describe, expect, it } from "vitest";

import { buildHighlightSegments, codePointSlice } from "@/lib/textOffsets";
import sampleResponse from "@/lib/__fixtures__/sampleAnalyzeResponse.json";
import unicodeResponse from "@/lib/__fixtures__/unicodeAnalyzeResponse.json";
import type { AnalyzeResponse } from "@/types/api";

const sample = sampleResponse as AnalyzeResponse;
const unicode = unicodeResponse as AnalyzeResponse;

describe("codePointSlice", () => {
  it("matches plain .slice() for ASCII text", () => {
    const text = "Hello, world!";
    expect(codePointSlice(text, 0, 5)).toBe("Hello");
    expect(codePointSlice(text, 7, 12)).toBe("world");
  });

  it("correctly slices text containing an astral character (emoji)", () => {
    // "😀" is one Unicode code point but two JS UTF-16 units -- a naive
    // .slice(start, end) using Python-style codepoint offsets would be
    // wrong here; codePointSlice must not be.
    const text = "😀 hi";
    // Python-style codepoint indices: [0]='😀', [1]=' ', [2]='h', [3]='i'
    expect(codePointSlice(text, 2, 4)).toBe("hi");
  });
});

describe("buildHighlightSegments — critical regression (item 24)", () => {
  it("every candidate's char_start/char_end slices back to its own text, for the real API fixture", () => {
    const segments = buildHighlightSegments(sample.normalized_text, sample.sentences.candidates);
    for (const candidate of sample.sentences.candidates) {
      expect(codePointSlice(sample.normalized_text, candidate.char_start, candidate.char_end)).toBe(candidate.text);
    }
    // Every candidate must appear as its own highlighted segment.
    const highlighted = segments.filter((s) => s.candidate !== null).map((s) => s.text);
    for (const candidate of sample.sentences.candidates) {
      expect(highlighted).toContain(candidate.text);
    }
  });

  it("reassembling all segments reproduces the original normalized_text exactly", () => {
    const segments = buildHighlightSegments(sample.normalized_text, sample.sentences.candidates);
    const reassembled = segments.map((s) => s.text).join("");
    expect(reassembled).toBe(sample.normalized_text);
  });

  it("holds for text containing an emoji (astral character) too", () => {
    for (const candidate of unicode.sentences.candidates) {
      expect(codePointSlice(unicode.normalized_text, candidate.char_start, candidate.char_end)).toBe(candidate.text);
    }
    const segments = buildHighlightSegments(unicode.normalized_text, unicode.sentences.candidates);
    expect(segments.map((s) => s.text).join("")).toBe(unicode.normalized_text);
  });

  it("skipped sentences' offsets are also valid against normalized_text", () => {
    for (const skipped of [...sample.sentences.skipped, ...unicode.sentences.skipped]) {
      const normalizedText = sample.sentences.skipped.includes(skipped)
        ? sample.normalized_text
        : unicode.normalized_text;
      expect(codePointSlice(normalizedText, skipped.char_start, skipped.char_end)).toBe(skipped.text);
    }
  });

  it("produces segments in ascending order even if candidates are passed unsorted", () => {
    const reversed = [...sample.sentences.candidates].reverse();
    const segments = buildHighlightSegments(sample.normalized_text, reversed);
    const highlightedStarts = segments
      .filter((s) => s.candidate !== null)
      .map((s) => s.candidate!.char_start);
    expect(highlightedStarts).toEqual([...highlightedStarts].sort((a, b) => a - b));
  });

  it("returns a single plain segment for no candidates", () => {
    const segments = buildHighlightSegments("Just plain text.", []);
    expect(segments).toEqual([{ text: "Just plain text.", candidate: null }]);
  });
});
