# Best Practices

## Route every model call through Elysia (`llm_client.py`)

Elysia handles OAuth2 token lifecycle, model routing, and provider (azure/aws) selection.
Direct provider calls bypass auth and cost controls — don't add them.

## Respect the two-stage cost model

- `gpt-5-mini` gates relevance (cheap); only articles scoring **75+** go to `gpt-4o` drafting.
- Don't drop the threshold gate or send everything to the expensive model — it controls spend.
- The threshold lives in `config.json`; change it there, deliberately.

## Keep humans in the loop

Drafts are **first drafts**. The editorial queue (approve/reject/edit/regenerate) and the
audit trail (`editorial_reviews`) exist so a human signs off before anything is published.
Don't auto-publish; preserve the review workflow.

## Dedup before classifying/drafting

URL-based dedup (`deduplicator.py`) avoids reprocessing and double-charging the LLM. Keep
fetch → dedup → classify → draft ordering in `ingestion_pipeline.py`.

## Cite sources

TSNN drafts include inline source citations and source attribution. Preserve provenance from
ingestion through draft so editors can verify claims.

## Configuration over code

Add/remove RSS feeds, sponsors, and tune `max_articles_per_feed` / thresholds / taxonomy in
`config.json`, not in module logic.

## Protect editorial surfaces

Editorial, analytics, and digest routes require login. Any new internal route handling drafts
or analytics should be `login_required` too.

## Handle external sources defensively

RSS feeds and NewsData.io can be flaky or change format. Fetch/parse should tolerate
individual source failures without aborting the whole run (log and continue).

## Database portability

Use SQLAlchemy models and `DATABASE_URL` so the same code runs on SQLite (dev) and PostgreSQL
(prod). Avoid SQLite- or Postgres-specific raw SQL.

## Stage vs prod Elysia

Defaults point at the **stage** Elysia stack. Switch `ELYSIA_API_BASE`/`ELYSIA_TOKEN_URL` to
prod hosts only with prod credentials — don't mix stage creds with prod endpoints.
