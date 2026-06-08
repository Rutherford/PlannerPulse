# Architecture

## Overview

A single Flask web app fronting two pipelines that share a SQLAlchemy data layer and a single
LLM gateway (Elysia).

```
                         app.py (Flask: routes, auth, dashboards)
                              │
        ┌─────────────────────┴───────────────────────┐
        ▼                                              ▼
 Editorial pipeline                            Newsletter pipeline
 ingestion_pipeline.py                         main.py (orchestrator)
   fetch (scraper.py / newsdata_fetcher.py)      scraper.py (RSS)
   → deduplicator.py (URL dedup)                 → summarizer.py (Elysia)
   → classifier.py  (gpt-5-mini, 0–100)          → deduplicator.py
   → tsnn_generator.py (gpt-4o draft)            → sponsor_manager.py
        │                                         → builder.py (HTML/MD/text)
        ▼                                              │
   scheduler.py (APScheduler 6am/12pm/6pm ET)          ▼
        │                                         output/ files
        └──────────────┬───────────────┬──────────────┘
                        ▼               ▼
                 llm_client.py     models.py / database.py
                 (Elysia OAuth2)   (SQLAlchemy; SQLite/Postgres)
```

## Components

| File | Responsibility |
|------|----------------|
| `app.py` | Flask app: all routes, Flask-Login auth, editorial/analytics/digest dashboards |
| `main.py` | Newsletter generation orchestrator |
| `llm_client.py` | Elysia client + OpenAI-compatible shim; handles OAuth2 client_credentials |
| `classifier.py` | TSNN relevance classifier (Elysia `gpt-5-mini`, scores 0–100) |
| `tsnn_generator.py` | TSNN draft generator (Elysia `gpt-4o`, structured JSON) |
| `ingestion_pipeline.py` | Editorial pipeline: fetch → dedup → classify → draft |
| `newsdata_fetcher.py` | Optional NewsData.io source integration |
| `scheduler.py` | APScheduler jobs (6 AM / 12 PM / 6 PM ET) |
| `scraper.py` | RSS feed scraping (feedparser / BeautifulSoup / trafilatura) |
| `summarizer.py` | Elysia article summarization + LLM client init |
| `builder.py` | HTML / Markdown / text newsletter builder |
| `deduplicator.py` | Article deduplication |
| `sponsor_manager.py` | Sponsor rotation (CVB/DMO) |
| `models.py` | SQLAlchemy models |
| `database.py` | DB session/managers (e.g. `DraftManager`) |
| `config.json` | Sources, sponsors, thresholds, topic taxonomy |
| `templates/`, `static/` | Jinja2 templates + Informa Connect design system |

## Data model (tables)

| Table | Purpose |
|-------|---------|
| `ingested_articles` | Every fetched article + relevance score, topic tags, status |
| `drafts` | AI-generated drafts with content, quality scores, editorial status |
| `editorial_reviews` | Audit trail of approve/reject/edit/regenerate actions |
| `articles` | Newsletter-pipeline article history |
| `newsletters` | Generated newsletter archive |

(Model classes in `models.py`: `Article`, `Newsletter`, `NewsletterArticle`, `Sponsor`,
`SponsorRotation`, `RSSSource`, `SystemSettings`, `IngestedArticle`, `Draft`,
`EditorialReview`.)

## Key design decisions

- **One LLM gateway.** Every model call goes through `llm_client.py` (Elysia + OpenAI-compatible
  shim). Don't call providers directly — Elysia handles auth, model routing, and provider
  selection (azure/aws).
- **Two-stage AI editorial flow.** Cheap model (`gpt-5-mini`) gates relevance; expensive model
  (`gpt-4o`) only drafts articles scoring 75+. This controls cost.
- **Config-driven sources & taxonomy.** `config.json` holds RSS sources, sponsors, thresholds,
  and the TSNN topic taxonomy — change behavior there, not in code, where possible.
- **DB-agnostic via SQLAlchemy + `DATABASE_URL`.** SQLite locally, PostgreSQL in production.
- **Scheduling decoupled.** `scheduler.py` triggers the same pipeline the manual button does.
