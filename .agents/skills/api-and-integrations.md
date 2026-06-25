# APIs & Integrations

## Elysia (Informa internal AI) — primary LLM gateway

- **Client:** `llm_client.py` exposes an OpenAI-compatible interface and handles the OAuth2
  client_credentials flow against the Informa IDP.
- **Endpoints (env-configurable):**
  - `ELYSIA_API_BASE` (default `https://api.stage.ai.informa.com`)
  - `ELYSIA_TOKEN_URL` (default `https://idp.dev.ai.informa.com/oauth2/token`)
  - `ELYSIA_SCOPE` (e.g. `elysia/api`)
- **Credentials:** `ELYSIA_APP_ID`, `ELYSIA_CLIENT_ID`, `ELYSIA_CLIENT_SECRET`.
- **Models used:** `gpt-5-mini` (classification), `gpt-4o` (drafts + feedback, default). Elysia
  can also route `gpt-5`, `claude-*`, `DeepSeek-V3-0324`; provider `azure`|`aws`.
- **Where called:** `classifier.py` (scoring), `tsnn_generator.py` (drafting), `summarizer.py`
  (newsletter summaries), and the AI Feedback flow — all via `llm_client.py`.

> Prod stack: switch `ELYSIA_API_BASE`/`ELYSIA_TOKEN_URL` to `api.ai.informa.com` /
> `idp.ai.informa.com` when prod credentials exist.

## NewsData.io (optional content source)

- `newsdata_fetcher.py`; enabled by setting `NEWSDATA_API_KEY`. Adds licensed news sources
  alongside RSS.

## RSS feeds (primary content source)

- Configured in `config.json` `sources` (7+ meetings/events publications).
- Fetched/parsed via `feedparser`, with `BeautifulSoup`/`trafilatura` for article extraction
  (`scraper.py`). `max_articles_per_feed` caps per-feed volume.

## Database

- SQLAlchemy over `DATABASE_URL`: SQLite (`planner_pulse.db`) for dev, PostgreSQL
  (`psycopg2-binary`) for prod. Access through `models.py` / `database.py` managers.

## Email/newsletter targets (output, not API)

- `builder.py` produces HTML/Markdown/text into `output/`, designed for Beehiiv, Mailchimp, or
  any HTML email editor. (No direct send integration in-repo.)

## Auth (inbound)

- Flask-Login session auth; admin credentials from `ADMIN_EMAIL`/`ADMIN_PASSWORD`/`ADMIN_NAME`.

## Adding an integration

Wrap the external service in its own module (like `newsdata_fetcher.py`), keep LLM calls in
`llm_client.py`, store results via the SQLAlchemy models, and make endpoints/keys
env-configurable.
