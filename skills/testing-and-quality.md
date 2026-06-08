# Testing & Quality

## Current state (be honest)

- **No automated test suite.** `test_app.py` is a *test/standalone variant of the Flask app
  "without OpenAI dependency"* — a manual harness, **not** pytest tests (it contains no
  `def test_*` functions). There is no test runner configured in `pyproject.toml`.
- **No linter/formatter config** (black/ruff/flake8) committed.
- **No CI** configuration present.

This is the verified state. Don't claim a passing test suite — there isn't one yet.

## What exists for quality today

- **Bug analysis docs:** `bug_analysis_and_fixes.md` and `bug_fixes_report.md` capture
  investigated issues and fixes — useful history when touching related code.
- **Runtime log:** `newsletter.log` records pipeline activity for after-the-fact debugging.
- **Human editorial review:** the approve/reject workflow + `editorial_reviews` audit trail is
  the primary quality gate on AI output.

## How to verify a change manually

1. Init a scratch DB: `DATABASE_URL=sqlite:///dev.db python models.py`.
2. Run the app: `... FLASK_PORT=5002 python app.py` and exercise the affected route.
3. For pipeline changes, use the manual "Run Pipeline" trigger and watch the live log /
   `newsletter.log`.
4. For LLM changes, confirm Elysia auth works and inspect a generated draft's structure
   (headline, `Zooming out:`/`By the numbers:`/`Bottom line:`, takeaways, citations).

## Recommended improvements (TODO)

- `TODO`: Add `pytest` with unit tests for `deduplicator`, `classifier` scoring parse,
  `builder` output, and `sponsor_manager` rotation — mocking `llm_client` so tests don't call
  Elysia.
- `TODO`: Add ruff/black config and a CI workflow.
- `TODO`: Rename/clarify `test_app.py` so it isn't mistaken for a pytest module.
