# Coding Standards

Derived from the existing code; no enforced linter/formatter config is committed, so match the
surrounding style.

## Python

- Python 3.11+, standard 4-space indentation.
- Each module opens with a docstring describing its role (see `app.py`, `builder.py`).
- Executable scripts use `#!/usr/bin/env python3` and a `"""..."""` header (e.g. `app.py`,
  `main.py`).
- Use the standard `logging` module; the app logs to `newsletter.log`.
- Load config from `.env` (via `python-dotenv`) and `config.json`; don't hardcode secrets,
  feeds, sponsors, or thresholds in code.

## Module boundaries (keep them)

- **All LLM access goes through `llm_client.py`.** Never call OpenAI/Azure/Anthropic/Elysia
  HTTP endpoints directly from feature code — use the shared client so OAuth2, model routing,
  and provider selection stay centralized.
- **All DB access goes through `models.py` / `database.py` managers** (e.g. `DraftManager`),
  not ad-hoc SQL.
- Keep the two pipelines separable: editorial (`ingestion_pipeline.py`) vs newsletter
  (`main.py`). Shared concerns (scraping, dedup, LLM, DB) live in their own modules.

## Flask

- Routes live in `app.py`. Protect editorial/analytics/digest routes with Flask-Login
  (`login_required`), matching existing protected routes.
- Render via Jinja2 templates in `templates/`; keep brand styling in `static/style.css`.

## Configuration over code

- RSS sources, sponsors, `max_articles_per_feed`, output formats, relevance threshold, and the
  TSNN topic taxonomy belong in `config.json`. Prefer editing config to changing logic.

## Data shapes

- SQLAlchemy models are the source of truth for stored data. When adding fields, update the
  model and the DB-init path (`python models.py`) together.

## Prompts

- TSNN draft/classification/feedback prompts encode editorial requirements (structure, voice,
  scoring rubric). Treat prompt changes as product changes — keep the documented output
  structure (`Zooming out:` / `By the numbers:` / `Bottom line:`, takeaways, alt headlines).
