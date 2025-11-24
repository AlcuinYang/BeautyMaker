# Contributing to Aesthetics Engine

This document captures the conventions and engineering practices to keep the codebase clear, consistent and easy to evolve.

## Principles

- Prefer explicit, readable code over clever one‑liners.
- Keep functions small and single‑purpose; name them after their intent.
- Handle errors close to the source; log actionable context, not secrets.
- Write docstrings for modules, classes and public functions.
- Type everything (function params, returns, and important locals) when practical.

## Python style

- Use Pydantic models for request/response contracts; validate early.
- Async I/O with `httpx`/`asyncio`; timeouts are mandatory for network calls.
- Structure providers under `services/generate/adapters/` with a single async `generate()` returning a normalized dict.
- Log with `logging` (module level logger), include key fields (mode/model/size/task_id), avoid printing secrets or API keys.
- In adapters, isolate:
  - payload building
  - submission
  - polling / result extraction

## Frontend style (React + TypeScript)

- Co-locate small, focused components under `frontend/src/components/`.
- Use `import type { ... }` for type‑only imports to speed up builds.
- Keep state hooks at component top; derive view data with `useMemo`.
- Extract network calls to `frontend/src/lib/api.ts`.
- Prefer composition over prop drilling; use small helper components.

## Comments & docs

- Module docstrings: intent, context, and how the module is used.
- Function docstrings: inputs, outputs, side‑effects.
- Inline comments: why, not what (avoid restating the code).

## Testing

- Use async tests via `httpx.AsyncClient + ASGITransport`.
- Keep tests hermetic: rely on adapters' fallbacks or mocked responses when tokens are missing.

## Commit / PR checklist

- [ ] Public functions/classes have docstrings
- [ ] New adapters log mode/model/size and mask secrets
- [ ] Timeouts and error handling present for network calls
- [ ] Types added/updated
- [ ] Tests pass locally

