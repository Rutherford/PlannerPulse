# Contributing

## Before you start

- Read [architecture.md](architecture.md), [domain-knowledge.md](domain-knowledge.md), and
  [best-practices.md](best-practices.md).
- Set up `.env` (Elysia creds, `DATABASE_URL`, admin login) and init the DB
  (`python models.py`).
- Skim `bug_analysis_and_fixes.md` / `bug_fixes_report.md` for context on past issues.

## Workflow

1. Branch for your change (don't commit to the default branch directly).
2. Implement, keeping module boundaries: LLM via `llm_client.py`, DB via `models.py`/
   `database.py`, config in `config.json`.
3. Verify manually (no test suite yet — see [testing-and-quality.md](testing-and-quality.md)):
   run the app, exercise the affected route, run the pipeline, inspect `newsletter.log` and a
   generated draft.
4. Update `skills/` docs when you change behavior, routes, models, or config schema.
5. Commit clearly. **Never commit** `.env`, `planner_pulse.db`, `newsletter.log`, or `output/`.

## Change checklist

- [ ] LLM calls go through `llm_client.py` (no direct provider calls).
- [ ] DB changes update `models.py` and the init/migration path together.
- [ ] New sources/sponsors/thresholds go in `config.json`, not code.
- [ ] Editorial/analytics/digest routes stay `login_required`.
- [ ] AI output remains human-reviewed (no auto-publish); audit trail preserved.
- [ ] Relevance gate + cost model intact (75+ threshold, gpt-5-mini → gpt-4o).
- [ ] Stage/prod Elysia hosts and credentials kept consistent.

## Good first improvements

- Add a real `pytest` suite (mock `llm_client`).
- Add ruff/black config and CI.
- Clarify `test_app.py` naming so it isn't mistaken for tests.
