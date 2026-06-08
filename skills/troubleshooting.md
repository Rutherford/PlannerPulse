# Troubleshooting

## Elysia / LLM

**Auth/401 from Elysia, or classification/drafts fail.**
- Check `ELYSIA_APP_ID`, `ELYSIA_CLIENT_ID`, `ELYSIA_CLIENT_SECRET` in `.env`.
- Confirm `ELYSIA_API_BASE` and `ELYSIA_TOKEN_URL` match the stack your credentials belong to
  (stage creds → stage hosts; prod creds → prod hosts). Mixing them fails OAuth.
- All LLM traffic flows through `llm_client.py`; check `newsletter.log` for the underlying error.

**No drafts generated even though articles were ingested.**
- Expected if nothing scored **75+**. Relevance gating (`gpt-5-mini`) only promotes high-scoring
  articles. Lower the threshold in `config.json` only if intended.

**Drafts missing structure / wrong voice.**
- A prompt or model change likely broke the TSNN output contract. Verify `tsnn_generator.py`
  still requests the labeled sections and alt headlines.

## Database

**`no such table` / model errors on first run.**
- Initialize the DB: `DATABASE_URL=... python models.py`.

**Switching to PostgreSQL fails.**
- Ensure `DATABASE_URL` is a valid Postgres URL and `psycopg2-binary` is installed (it's a
  dependency). Re-run the init/migration against the new DB.

## Scheduler

**Pipeline isn't running automatically.**
- APScheduler runs **in-process** — the app (`app.py`) must be running for the 6 AM / 12 PM /
  6 PM ET jobs to fire. If the process is down, schedules don't run. Use the manual "Run
  Pipeline" button to test on demand.

## Sources / scraping

**A feed returns nothing or errors.**
- RSS sources change format and go down. Check the specific URL in `config.json`; a single bad
  feed shouldn't abort the run — confirm errors are logged and skipped.

**NewsData.io not contributing sources.**
- `NEWSDATA_API_KEY` must be set; without it `newsdata_fetcher.py` is skipped (RSS-only).

## App / auth

**Can't log into editorial pages.**
- Set `ADMIN_EMAIL`/`ADMIN_PASSWORD` (and `SECRET_KEY` for sessions) in `.env`. Defaults in the
  README are placeholders.

**Port already in use.**
- Change `FLASK_PORT` (default 5002).

## Where to look first

`newsletter.log` → `llm_client.py` (LLM/auth) → `ingestion_pipeline.py` (pipeline order) →
`config.json` (sources/thresholds) → `models.py`/`database.py` (data).
Also check `bug_analysis_and_fixes.md` for previously-diagnosed issues.
