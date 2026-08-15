/**
 * Utilities for slicing `normalized_text` using the API's
 * `char_start`/`char_end` offsets (Phase C/E's invariant:
 * normalized_text[char_start:char_end] === candidate.text).
 *
 * IMPORTANT: the backend computes these offsets as Python string
 * indices, which count Unicode CODE POINTS. JavaScript's native string
 * indexing (`.slice()`, `.length`) counts UTF-16 CODE UNITS instead --
 * these differ for any "astral" character (code point > U+FFFF, which
 * includes most emoji): such a character is ONE Python index but TWO
 * JS UTF-16 units (a surrogate pair). Naively calling
 * `normalizedText.slice(start, end)` would silently produce wrong
 * results for any text after such a character. Every slice in this
 * module goes through `Array.from()` instead, which iterates a string
 * by code point (correctly pairing surrogates) -- this keeps the
 * invariant correct for any input, not just plain ASCII/Latin text.
 */

export function codePointSlice(text: string, start: number, end: number): string {
  return Array.from(text).slice(start, end).join("");
}

export interface HighlightRange {
  char_start: number;
  char_end: number;
}

export interface HighlightSegment<T extends HighlightRange> {
  text: string;
  candidate: T | null;
}

/**
 * Splits `normalizedText` into an ordered sequence of segments, each
 * either plain text or a highlighted candidate range. Candidates are
 * sorted by `char_start` before splitting; overlapping ranges are not
 * expected (sentence candidates are non-overlapping by construction)
 * and are not specially handled beyond processing them in order.
 */
export function buildHighlightSegments<T extends HighlightRange>(
  normalizedText: string,
  candidates: T[],
): HighlightSegment<T>[] {
  const codepoints = Array.from(normalizedText);
  const sorted = [...candidates].sort((a, b) => a.char_start - b.char_start);

  const segments: HighlightSegment<T>[] = [];
  let cursor = 0;

  for (const candidate of sorted) {
    if (candidate.char_start > cursor) {
      segments.push({
        text: codepoints.slice(cursor, candidate.char_start).join(""),
        candidate: null,
      });
    }
    segments.push({
      text: codepoints.slice(candidate.char_start, candidate.char_end).join(""),
      candidate,
    });
    cursor = Math.max(cursor, candidate.char_end);
  }

  if (cursor < codepoints.length) {
    segments.push({ text: codepoints.slice(cursor).join(""), candidate: null });
  }

  return segments;
}
