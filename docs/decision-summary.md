# Decision Summary

Quick-reference table for reviewers. Full reasoning lives in
[`decisions/`](decisions/).

| ID | Decision | Chosen Approach | Main Alternative | Why |
|----|----------|------------------|-------------------|-----|
| DEC-001 | Backend | FastAPI (Python) | Node.js/Express | Whole ML stack (Transformers, spaCy, scikit-learn) is Python-only; avoids a cross-language boundary just to reach the model |
| DEC-002 | Frontend | Next.js + TypeScript + Tailwind | Plain React + Vite | Matches the actual UI shape (few views, composable evidence widgets) and the brief's recommendation |
| DEC-003 | Repo layout | Single monorepo | Separate repos per component | Keeps code, docs, decisions, and experiments cross-referenceable in one tree |
| DEC-004 | Language model role | Local LM as feature-extraction instrument only; scoring is our own code | LLM-as-classifier | Explainability requires measurable features, not an opaque verdict; local-only avoids paid API dependency |
| DEC-005 | Sentence segmentation | spaCy `en_core_web_sm` statistical pipeline | Regex/rule-based splitting | Handles abbreviations/punctuation correctly; same pipeline reused for Phase 3 POS/dependency features, keeping boundaries consistent |

This table will grow through later phases (feature selection, scoring
method, calibration, dataset splitting, fairness methodology, etc.) as
those decisions are made and recorded.
