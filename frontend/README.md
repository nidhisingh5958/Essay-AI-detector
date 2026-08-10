# Frontend — AI Detector for Admissions Essays

Next.js (App Router) + TypeScript + Tailwind CSS.

This is the presentation layer only: paste essay → call `/api/analyze` on the
backend → render sentence/passage evidence. It holds no scoring logic of its
own.

See the repository root [README.md](../README.md) and [docs/architecture.md](../docs/architecture.md)
for the full system design, setup instructions, and reasoning trail.

## Local development

```bash
npm install
npm run dev
```

Requires the backend running at `http://localhost:8000` (see `backend/README`
instructions in the root README).
