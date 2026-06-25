# Glossary

## Platform / AI

- **Elysia:** Informa's internal AI platform (`api.stage.ai.informa.com`). All LLM calls route
  through it via an OpenAI-compatible shim (`llm_client.py`), authenticated with OAuth2
  client_credentials against the Informa IDP.
- **App ID (`ELYSIA_APP_ID`):** Registered application identifier for Elysia.
- **Provider:** Backend Elysia routes to — `azure` or `aws`.
- **gpt-5-mini:** Cheap-tier model used for relevance classification (0–100).
- **gpt-4o:** Default model used for draft generation and AI editorial feedback.

## Editorial / TSNN

- **TSNN:** Trade Show News Network — the editorial brand the assistant writes for.
- **Relevance score:** 0–100 score of an article against the TSNN taxonomy; 75+ proceeds to drafting.
- **Topic taxonomy:** The TSNN topic set (Trade Show Operations, Venues & Convention Centers,
  Event Technology, Industry Organisations, Major Organisers, M&A, Market Data).
- **Draft:** AI-generated, publication-ready first article in TSNN's voice.
- **Editorial queue:** The review dashboard (`/editorial`) for approve/reject/edit/regenerate.
- **AI Feedback:** Structured GPT-4o quality review of a draft.
- **Digest (`/digest`):** Morning briefing of pending drafts and next run times.

## Newsletter

- **Planner Pulse:** The newsletter product (curated meetings-industry digest).
- **Source diversity:** Round-robin interleaving capping outlets at ~2 articles each.
- **Sponsor rotation:** Cycling configured sponsor messages into the newsletter.
- **CVB / DMO:** Convention & Visitors Bureau / Destination Marketing Organization — the
  sponsor type (e.g. Visit Orlando).
- **Beehiiv / Mailchimp:** Email platforms the HTML output targets.

## Sources / data

- **NewsData.io:** Optional licensed news API source (`NEWSDATA_API_KEY`).
- **feedparser / trafilatura / BeautifulSoup:** RSS parsing + article text extraction.
- **`ingested_articles` / `drafts` / `editorial_reviews`:** Core DB tables.

## Infra

- **APScheduler:** In-process scheduler running the pipeline at 6 AM / 12 PM / 6 PM ET.
- **Flask-Login:** Session auth protecting editorial surfaces.
- **`DATABASE_URL`:** Selects SQLite (dev) vs PostgreSQL (prod).
- **Replit (`.replit`, `replit.md`):** The project's original hosting environment.
