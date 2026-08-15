# Frontend — Phase F

**Status: executed 2026-08-15.** Turns the Phase 1 landing-page scaffold
into a complete, working analysis experience against the frozen
[production API](api.md) (Phase E). No detector code, feature
extraction, evidence mapper, threshold, or research artifact was
touched in this phase — this document describes presentation/
integration work only.

## Architecture

```
app/page.tsx (orchestrator)
  │
  ├─ lib/useEssayAnalysis.ts   -- explicit state model (idle/validating/analyzing/success/error)
  │    └─ lib/api.ts           -- the ONLY module that calls POST /api/analyze
  │         └─ types/api.ts    -- TypeScript types mirroring the backend response exactly
  │
  ├─ components/EssayInput/EssayInput.tsx     -- textarea + Analyze button (controlled, no logic)
  ├─ components/StatusMessage/StatusMessage.tsx -- loading/error banners
  ├─ components/ResultsSummary/ResultsSummary.tsx -- essay-level state + score + evidence
  ├─ components/EssayViewer/EssayViewer.tsx    -- highlighted passages (uses lib/textOffsets.ts)
  │    └─ components/EvidencePanel/EvidencePanel.tsx -- reused for both essay- and sentence-level evidence
  └─ components/Limitations/Limitations.tsx    -- fixed honesty section
```

**No new UI library was introduced** — everything uses the existing
Tailwind v4 setup already in the repo. **No global state library** was
added — a single custom hook (`useEssayAnalysis`) is sufficient for this
one-page flow. `components/FeatureBreakdown/` remains an empty
placeholder, deliberately: per the earlier product audit
([PRODUCT-AUDIT.md](PRODUCT-AUDIT.md) §9), a separate dense feature
dashboard was recommended against — evidence is folded into
`EvidencePanel` instead, reused wherever evidence needs to be shown.

## User flow

```
Paste essay
    ↓
Analyze (disabled until non-empty text is present)
    ↓
POST /api/analyze  (lib/api.ts, the only fetch call in the app)
    ↓
Essay-level result (ResultsSummary) — state, evidence, limitation note
    ↓
Ranked candidate passages (EssayViewer) — highlighted in the essay text, each with its own evidence
    ↓
Limitations (always visible once an analysis completes)
```

## Result-state semantics (unchanged from Phase D/E)

| Backend state | Displayed label | Never displayed |
|---|---|---|
| `machine_signal_detected` | "Machine-generated signal detected" | "73% AI", "AI probability: 73%" |
| `no_strong_signal_detected` | "No strong machine-generated signal detected" | — |
| `inconclusive` | "Inconclusive" | a fabricated score (none is shown when `score` is `null`) |

The raw `score`, when present, is always labeled *"Detector score...
not a probability that AI wrote this essay"* — never presented as a
bare percentage or authorship probability (enforced by test:
`ResultsSummary.test.tsx`'s "never displays a raw '% AI'..." case).

State is conveyed by **text label + icon glyph**, with color as a
secondary reinforcement only (WCAG "not by color alone" —
`STATE_CONFIG` in `ResultsSummary.tsx`).

## Sentence highlighting — the offset invariant

`EssayViewer` renders `normalized_text` with `char_start`/`char_end`
from the API used **exactly as returned** — no re-tokenizing, no
recomputed sentence boundaries in JavaScript (Phase F item 10).

**A real cross-language subtlety, handled explicitly**: the backend
computes offsets as Python string indices, which count Unicode **code
points**. JavaScript's native string indexing (`.slice()`, `.length`)
counts UTF-16 **code units** instead — these diverge for any "astral"
character (code point > U+FFFF, e.g. most emoji), which is one Python
index but a surrogate *pair* (two JS units). `lib/textOffsets.ts`'s
`codePointSlice`/`buildHighlightSegments` always slice via
`Array.from()` (which iterates by code point) specifically to stay
correct for this case — verified by test against a real API response
fixture containing an emoji
(`lib/__tests__/textOffsets.test.ts`, "holds for text containing an
emoji").

Every candidate's label reads **"Potentially AI-assisted passage"** —
never "AI-written sentence" or any authorship-certainty phrasing
(enforced by test).

## Evidence presentation

`EvidencePanel` renders only the backend's already-composed
`human_label` and `statement` — never a raw internal feature name like
`stylo_type_token_ratio`. The frontend performs zero interpretation of
feature values; it displays exactly what the deterministic evidence
mapper (DEC-017, Phase D) already produced.

## Error / loading states

| State | UI |
|---|---|
| Empty/whitespace input | Analyze button stays disabled; if `analyze()` is somehow called anyway, a client-side message ("Please enter some essay text to analyze.") — no network call made |
| Request in flight | "Analyzing essay…" banner (`StatusMessage`, `role="status"`, `aria-live="polite"`) |
| API error (422/413/500/503/network failure) | Red `role="alert"` banner with the backend's own `detail` message (or a client-side network-failure message) — never a raw stack trace or filesystem path, verified by test |
| No scorable sentences | `EssayViewer` shows an explicit "No candidate passages could be evaluated..." message, using the API's `no_evidence_reason` when present — never a blank section |
| Skipped sentences exist | A visible "Some passages could not be scored..." note — never silently hidden |

## Accessibility (Phase F item 18)

- Textarea has an explicit associated `<label>` (visually hidden, but
  present for screen readers) — `screen.getByLabelText(/essay text to
  analyze/i)` passes.
- The Analyze button is a real semantic `<button>`, keyboard-focusable
  and keyboard-activatable (native behavior) — disabled via the native
  `disabled` attribute, not a styling-only fake-disabled state.
- Highlighted passages are also reachable via keyboard (`tabIndex={0}`,
  `role="button"`, `Enter`/`Space` handling) since a `<mark>` element
  has no native interactivity of its own.
- Loading/error banners use `role="status"`/`role="alert"` with
  appropriate `aria-live` so screen readers announce state changes.
- Result state is never conveyed by color alone (text label + icon
  glyph always present).
- Sufficient text contrast: reused the existing Tailwind zinc/amber/
  emerald palette already used in the Phase 1 scaffold, at standard
  Tailwind shade pairings chosen for light/dark contrast.

## Privacy (Phase F item 21)

Essay text is **never** written to `localStorage`, cookies, or any
analytics/telemetry — it exists only in React component state for the
duration of the session and is sent to exactly one place: this
project's own `POST /api/analyze` (`lib/api.ts`). No external AI API is
called from the frontend, ever — the only network call the frontend
makes is to the local `NEXT_PUBLIC_API_BASE_URL`.

## Local development

```bash
# Backend (from backend/)
source .venv/bin/activate
uvicorn app.main:app --port 8000

# Frontend (from frontend/)
npm install
npm run dev
```

The frontend calls `NEXT_PUBLIC_API_BASE_URL` (default
`http://localhost:8000`, see `.env.local.example`) — copy that file to
`.env.local` and adjust if the backend runs elsewhere. **Not a secret**
— `NEXT_PUBLIC_` variables are bundled into client-side JavaScript by
Next.js design.

CORS: unchanged from Phase 1/E —
`backend/app/main.py` allows `http://localhost:3000` only.

## Testing

No frontend test framework existed before this phase (a real gap
identified in [PRODUCT-AUDIT.md](PRODUCT-AUDIT.md) §17). Added: Vitest
+ React Testing Library + jsdom (`vitest.config.ts`, `vitest.setup.ts`,
`npm test`). **46 new tests**, across 7 files:

- `lib/__tests__/textOffsets.test.ts` — the critical offset-mapping
  regression (item 24), including the emoji/astral-character case.
- `lib/__tests__/api.test.ts` — success/error/network-failure handling,
  no leaked internals.
- `lib/__tests__/useEssayAnalysis.test.ts` — state-machine transitions.
- `components/EssayInput/__tests__/EssayInput.test.tsx` — button
  enable/disable, loading state, accessible label.
- `components/ResultsSummary/__tests__/ResultsSummary.test.tsx` — all
  three states, no raw "% AI" claims, no research statistics as
  per-input confidence.
- `components/EssayViewer/__tests__/EssayViewer.test.tsx` — highlighting,
  skipped-sentence reporting, no-evidence state, Unicode.
- `app/__tests__/page.test.tsx` — full integration flow (idle → analyze
  → success/error → repeated analysis), keyboard-accessible controls.

**Test fixtures** (`lib/__fixtures__/*.json`) are **real captured API
responses** from the actual backend (via `TestClient`), not hand-written
mock JSON — so frontend tests exercise the real response shape, not an
assumed one.

## Known non-blocking items

- A Vite config warning ("ESM syntax loaded as CommonJS") appears when
  running tests — cosmetic, does not affect test correctness or the
  production build; not addressed to avoid an unrelated risk to
  Next.js's own config loading.
- No visual/interactive browser session was available in this
  environment to manually click through the UI. Verified instead via:
  46 passing automated tests (jsdom-rendered real component trees), a
  clean production build (`next build`), and a live end-to-end smoke
  test (both dev servers started, a real `curl` POST to `/api/analyze`
  with the frontend's `Origin` header, confirming CORS and the full
  response shape match what the components expect). This is disclosed
  explicitly, not presented as equivalent to manual browser testing.
