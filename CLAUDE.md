# CLAUDE.md

Guidance for AI assistants (and humans) working in the PlannerPulse repository.

## What this project is

PlannerPulse is a Python/Flask application that automates editorial content for the
meetings, events, and trade-show industry. It scrapes industry news, scores and
summarizes it with OpenAI, and produces reviewable output. The codebase contains
**two related-but-distinct pipelines** that share infrastructure (config, database,
OpenAI client, RSS scraper). Understand which one you are touching before editing:

1. **Planner Pulse newsletter generator** (the original product)
   - Entry point: `main.py` (CLI) and the dashboard/`/generate` route in `app.py`.
   - Flow: `scraper.fetch_articles` → dedupe via `DatabaseArticleManager` → source
     diversification (`main.diversify_articles`) → `summarizer.summarize_article`
     (GPT-4o) → `summarizer.generate_subject_line` → `builder.build_newsletter`
     (HTML/Markdown/text) → persisted by `DatabaseNewsletterManager`, sponsor rotated
     by `DatabaseSponsorManager`.
   - Output written to `output/newsletter.{html,md,txt}`.

2. **TSNN AI Editorial Assistant** (newer, added in the `tsnn-editorial-assistant` work)
   - Entry point: `ingestion_pipeline.run_editorial_pipeline`, triggered by the
     `scheduler` (6 AM / 12 PM / 6 PM ET) or the `/api/editorial/ingest` route.
   - Flow: `scraper.fetch_articles` (+ optional `newsdata_fetcher`) → dedupe + persist
     as `IngestedArticle` via `DraftManager` → `classifier.classify_article`
     (GPT-4o-mini, 0–100 relevance) → for articles ≥ `draft_threshold`,
     `tsnn_generator.generate_draft` (GPT-4o) produces a structured `Draft` →
     human review in the `/editorial` dashboard (approve / reject / edit / regenerate /
     AI assist) → export as HTML/Markdown/text.
   - This pipeline is for the **TSNN (Trade Show News Network)** editorial voice and is
     separate from the meeting-planner newsletter.

Both are served by the single Flask app in `app.py`.

## Repository layout

```
app.py                  # Flask web app: dashboard, settings API, editorial/analytics/digest routes, auth
main.py                 # CLI orchestration for the newsletter generator pipeline
scheduler.py            # APScheduler background jobs that run the editorial pipeline
ingestion_pipeline.py   # TSNN pipeline orchestration (fetch → classify → draft)

scraper.py              # RSS fetching (feedparser + requests) with trafilatura full-text fallback
newsdata_fetcher.py     # Optional NewsData.io source for the TSNN pipeline
classifier.py           # TSNN relevance scoring (0–100) + score_label/score_color helpers
summarizer.py           # OpenAI client init + newsletter summaries & subject lines
tsnn_generator.py       # TSNN draft generation/regeneration + draft→HTML/Markdown export
builder.py              # Renders the newsletter into HTML (Jinja2)/Markdown/text
deduplicator.py         # LEGACY JSON-file deduplicator (superseded by DB managers; kept for migration)

models.py               # SQLAlchemy models + engine/session helpers + init_database()
database.py             # All DB-backed managers (article, sponsor, newsletter, RSS, DraftManager)

config.json             # Runtime configuration (sources, sponsors, thresholds, topics) — read AND written at runtime
.env.example            # Documented environment variables; copy to .env

templates/              # Jinja2 templates: preview, editorial, analytics, digest, login, base_template (email)
static/style.css        # Brand styling (PlannerPulse palette + Inter font)
output/                 # Generated newsletter files (gitignored)
data/                   # Legacy JSON state + backups (gitignored)
test_app.py             # A mock Flask app (no OpenAI/DB) for offline UI testing — NOT a pytest suite
README.md / replit.md   # Human-facing docs (some details are aspirational/out of date — see notes below)
```

## Running the project

This project uses **uv** (`uv.lock`, `pyproject.toml`). Python 3.11+ and a PostgreSQL
database are required.

```bash
uv sync                          # install dependencies
cp .env.example .env             # then fill in DATABASE_URL, OPENAI_API_KEY, admin creds
python models.py                 # create database tables (init_database)
python app.py                    # start the Flask web app (default 127.0.0.1:5000)
python main.py                   # run the newsletter generator from the CLI
```

- The web app starts the editorial scheduler automatically on launch.
- `test_app.py` runs a dependency-free mock of the dashboard (`python test_app.py`),
  useful for working on templates without OpenAI/DB access.
- There is **no `requirements.txt`** despite the README mentioning one; use `uv`.
- There is **no automated test suite** and no linter/formatter config. If you add
  tests, prefer `pytest` and put them in clearly named `test_*.py` files (note
  `test_app.py` is already taken by the mock app).

## Configuration & secrets

- **`config.json`** holds non-secret runtime config: `sources` (RSS URLs), `sponsors`,
  `email_settings`, `content_settings`, `relevance_threshold` (default 60),
  `draft_threshold` (default 75), `tsnn_topics`, NewsData query, etc. Several `app.py`
  settings endpoints **write back** to this file, so treat it as mutable runtime state,
  not just a static config.
- **Secrets only come from environment variables** (see `.env.example`):
  - `DATABASE_URL` (PostgreSQL), `OPENAI_API_KEY` — required.
  - `ADMIN_EMAIL` + (`ADMIN_PASSWORD_HASH` bcrypt, preferred) or `ADMIN_PASSWORD`
    (dev-only) for the single-admin login.
  - `SECRET_KEY` (Flask sessions), `ADMIN_NAME`, `NEWSDATA_API_KEY` (optional),
    `FLASK_HOST` / `FLASK_PORT` / `FLASK_DEBUG`.
- **Never** put the OpenAI key in `config.json`. `summarizer.get_api_key()` deliberately
  reads only from the environment to avoid committing secrets. The `/api/settings/api-key`
  route stores it in `os.environ` for the session only.
- `.env`, `output/`, `data/`, and `*.log` are gitignored. Do not commit secrets or
  generated artifacts.

## Database conventions

- Models live in `models.py`; there are **two model groups** sharing one `Base`/database:
  - Newsletter side: `Article`, `Newsletter`, `NewsletterArticle`, `Sponsor`,
    `SponsorRotation`, `RSSSource`, `SystemSettings`.
  - TSNN editorial side: `IngestedArticle`, `Draft`, `EditorialReview`.
- All data access goes through **manager classes in `database.py`**, never raw queries in
  routes (the `analytics` route is the main exception, querying directly for charts).
- Managers follow a consistent pattern: lazy `session` property, `close_session()`,
  context-manager support (`__enter__`/`__exit__`), and a `__del__` safety net. Prefer
  using them as context managers (`with DatabaseArticleManager() as am:`) as `main.py`
  and the dashboard do. Each manager method wraps work in try/except with
  `session.rollback()` on failure and returns `None`/`False`/`[]` rather than raising.
- Schema changes: there is **no migrations framework** (no Alembic). Tables are created
  by `Base.metadata.create_all` via `models.init_database()` (`python models.py`).
  Adding a column to an existing table requires a manual migration. `migrate_from_json`
  (in `models.py`) exists only for the one-time legacy JSON → DB import.

## OpenAI usage conventions

- A single global client lives in `summarizer.py` (`openai_client`, initialized from the
  env key). Other modules reach it via `from summarizer import openai_client`.
- **Models in use** (be deliberate before changing):
  - `gpt-4o` — newsletter summaries, subject lines, TSNN draft generation/regeneration,
    and the `/api/editorial/assist` editor review.
  - `gpt-4o-mini` — relevance classification (`classifier.py`) and the API connectivity
    test (`summarizer.test_api_connection`).
  - `summarizer.py` contains an explicit comment "do not change this unless explicitly
    requested by the user" regarding the model. Honor that — don't silently bump models.
- Structured outputs use `response_format={"type": "json_object"}` and the code expects
  specific JSON keys (see the prompts in `classifier.py` and `tsnn_generator.py`). If you
  change a prompt's output schema, update the consuming code (`DraftManager.save_draft`,
  `_draft_to_dict`, etc.) accordingly.

## Auth & web conventions

- Auth is **Flask-Login with a single in-memory admin user** (`EditorUser` in `app.py`),
  credentials from env. Mutating/editorial routes are protected with `@login_required`;
  the public dashboard (`/`) and `/preview` are not.
- API routes return JSON (`401` for unauthorized under `/api/`); browser routes redirect
  to `/login`. Follow this split when adding routes.
- Input validation helpers (`validate_url`, `validate_string`, `sanitize_json_input`) and
  length constants live at the top of `app.py` — reuse them for new endpoints.
- Security hardening already in place (keep it): session-cookie flags,
  open-redirect protection on login `next`, directory-traversal guard in
  `/output/<filename>`. Don't regress these.

## Editorial pipeline details worth knowing

- `relevance_threshold` (≥ score → "relevant", logged) vs `draft_threshold`
  (≥ score → a draft is generated). Below `relevance_threshold` the `IngestedArticle`
  is archived.
- `IngestedArticle.status`: `pending` → `classified` → `draft_generated` / `archived`.
  The pipeline re-picks up stale `pending` records (e.g. saved before the API key was set).
- `Draft.status`: `draft` → `approved` / `rejected` (and `in_review`/`published` defined
  but lightly used). Every editor action is logged to `EditorialReview` for the analytics
  dashboard.
- The scheduler uses `America/New_York` cron triggers; `get_next_run_times()` feeds the
  digest page.

## Style & conventions to match

- Plain, module-level functions for pipeline steps; class-based managers for stateful DB
  access. Match the surrounding style of the file you edit.
- Logging via the stdlib `logging` module (`logger = logging.getLogger(__name__)`),
  not `print`. The app logs to `newsletter.log` and stdout.
- Type hints and docstrings are used throughout — keep adding them.
- Article dicts are passed around with loosely-shared keys across both pipelines
  (`title`, `link`/`external_url`, `summary`, `content`/`full_content`, `source`/
  `source_name`, `published`/`published_at`). When normalizing a new source, match this
  shape (see `newsdata_fetcher.fetch_newsdata_articles` for the canonical example).

## Gotchas / known inaccuracies

- README/replit.md describe some features aspirationally (e.g. `requirements.txt`,
  "async-ready"); trust the code over the prose. `replit.md` "Recent Changes" predates the
  TSNN editorial assistant — the editorial pipeline, scheduler, auth, and analytics are
  newer.
- `bug_analysis_and_fixes.md` and `bug_fixes_report.md` are historical change logs, not
  current TODOs.
- `deduplicator.py` (JSON-based) is legacy; new dedup happens in the DB managers
  (`DatabaseArticleManager.is_duplicate`, `DraftManager.is_duplicate_url`).
- This is a Replit-originated project (`.replit`, `pyproject.toml` name
  `repl-nix-workspace`); the runButton starts `python app.py`.

## Git workflow

- Active development branch for this work: `claude/claude-md-docs-AzhIz`. Develop, commit,
  and push there; do not push to `main` without explicit permission.
- Do not open a pull request unless explicitly asked.
