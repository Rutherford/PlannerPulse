# PlannerPulse

**AI-Powered Newsletter Generator & Editorial Assistant for the Meetings Industry**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1+-green.svg)](https://flask.palletsprojects.com)
[![Elysia](https://img.shields.io/badge/AI-Elysia%20%28Informa%29-orange.svg)](https://api.stage.ai.informa.com/v1/ai/docs)
[![SQLite / PostgreSQL](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-336791.svg)](https://postgresql.org)

PlannerPulse is an internal editorial intelligence tool for the meetings and events industry, built for Informa Connect. It combines automated news ingestion, AI-powered relevance classification, TSNN-style draft article generation, and a full editorial review workflow — all in a single Flask web application.

All LLM calls are routed through **Elysia**, Informa's internal AI platform (`api.stage.ai.informa.com`), authenticated via OAuth2 client_credentials against the Informa IDP.

---

## What It Does

PlannerPulse runs two parallel workflows:

**Newsletter Generator** — Fetches articles from configured RSS feeds, summarises them with Elysia (GPT-4o by default), applies source-diversity balancing, and produces a professionally formatted HTML/Markdown/text newsletter ready for Beehiiv, Mailchimp, or any HTML email editor.

**TSNN AI Editorial Assistant** — An internal newsroom tool that monitors industry sources, scores every article for TSNN relevance (0–100), generates publication-ready first drafts in TSNN's editorial voice, and presents them in a review dashboard with approve / reject / regenerate / export / AI feedback actions.

---

## Features

### Editorial Pipeline (TSNN AI Assistant)

- **Relevance Classification** — Elysia's `gpt-5-mini` (the cheap-tier model) scores every ingested article 0–100 against TSNN's topic taxonomy (Trade Show Operations, Venues & Convention Centers, Event Technology, Industry Organisations, Major Organisers, M&A, Market Data). Only articles scoring 75+ proceed to draft generation.
- **TSNN-Style Draft Generation** — Elysia's `gpt-4o` generates full articles using the TSNN AI Editorial Assistant PRD prompts: data-forward headline, news lede, structured body (`Zooming out:`, `By the numbers:`, `Bottom line:`), *Why This Matters to Event Professionals*, and 3–5 key takeaway bullets with inline source citations.
- **Alternative Headlines** — Every draft includes 2 alternative headline angles selectable with one click.
- **Editorial Review Queue** — Split-panel dashboard (queue left, full article detail right). Filter by Pending / Approved / Rejected.
- **Approve / Reject / Edit / Regenerate** — One-click approve; reject with categorised reason (Not relevant, Inaccurate, Tone mismatch, Already covered, etc.); inline headline + body editing; regenerate with free-text editor instructions.
- **AI Editorial Feedback** — "AI Feedback" button sends the draft to Elysia (GPT-4o) for a structured quality review: Overall score, TSNN Voice score, Strengths, Issues (with severity), Missing Context, and Suggested Improvements.
- **Export** — Approved drafts export as CMS-ready HTML, Markdown, or plain text.
- **URL-Based Deduplication** — Articles already in the database are skipped; previously unclassified articles are picked up and classified on subsequent runs.
- **NewsData.io Integration** — Optional: set `NEWSDATA_API_KEY` to add 87,000+ licensed news sources alongside RSS feeds.

### Automation & Scheduling

- **APScheduler** — Pipeline runs automatically at 6:00 AM, 12:00 PM, and 6:00 PM ET when the app is running.
- **Manual Trigger** — "Run Pipeline" button in the Editorial Queue fires an on-demand run with a live terminal-style log.

### Daily Digest

`/digest` — An editorial morning briefing showing all pending drafts with relevance scores, source attribution, next scheduled run times, and direct review links. Approved articles ready for export are listed separately.

### Analytics Dashboard

`/analytics` — Pipeline performance with Chart.js charts:
- Approval rate and total reviewed
- Drafts generated over the last 14 days
- Topic distribution (donut chart)
- Top sources by article volume
- Rejection reason breakdown
- Average relevance score

### Newsletter Generator

- RSS scraping from 7+ industry publications
- Source diversity filter — round-robin interleaving (max 2 articles per outlet)
- Elysia summarisation with key takeaway extraction
- AI-generated subject lines
- Sponsor rotation with CVB/DMO support
- Professional HTML output using Informa Connect brand styling (Georgia serif masthead, editorial article layout)

### Authentication

- Flask-Login session-based auth protecting all editorial tools
- Credentials configured via environment variables
- Login page at `/login`; sign-out in every sidebar

---

## Quick Start

### Prerequisites

- Python 3.11+
- Elysia credentials issued by the Informa Connect AI / Elysia onboarding team:
  - `app_id` (registered application identifier)
  - OAuth2 `client_id` and `client_secret` for the Informa IDP
- NewsData.io API key (optional)

### Installation

```bash
git clone https://github.com/MacKitchin/PlannerPulse.git
cd PlannerPulse

# Install dependencies
uv sync
# or: pip install -e .

# Initialise the database
DATABASE_URL=sqlite:///planner_pulse.db python models.py
```

### Environment Variables

Create a `.env` file:

```
# Required — Elysia (Informa AI) credentials
ELYSIA_APP_ID=your-app-id
ELYSIA_CLIENT_ID=your-client-id
ELYSIA_CLIENT_SECRET=your-client-secret

# Optional — Elysia stack pointers (defaults shown). Switch to prod hosts
# (api.ai.informa.com / idp.ai.informa.com) once prod credentials are issued.
ELYSIA_API_BASE=https://api.stage.ai.informa.com
ELYSIA_TOKEN_URL=https://idp.dev.ai.informa.com/oauth2/token
# ELYSIA_SCOPE=elysia/api
# ELYSIA_DEFAULT_MODEL=gpt-4o            # gpt-4o | gpt-5 | gpt-5-mini | claude-* | DeepSeek-V3-0324
# ELYSIA_DEFAULT_PROVIDER=azure          # azure | aws
# ELYSIA_COLLECTION=content_vectorstore

# Database (SQLite for local dev, PostgreSQL for production)
DATABASE_URL=sqlite:///planner_pulse.db

# Editorial login
ADMIN_EMAIL=admin@plannerpulse.com
ADMIN_PASSWORD=changeme
ADMIN_NAME=Editorial Team

# Optional
NEWSDATA_API_KEY=...
SECRET_KEY=change-in-production
FLASK_PORT=5002
```

### Run

```bash
DATABASE_URL=sqlite:///planner_pulse.db FLASK_PORT=5002 python app.py
```

| URL | Description |
|---|---|
| `http://localhost:5002/` | Newsletter Dashboard |
| `http://localhost:5002/editorial` | Editorial Queue *(login required)* |
| `http://localhost:5002/analytics` | Analytics Dashboard *(login required)* |
| `http://localhost:5002/digest` | Daily Digest *(login required)* |

---

## Project Structure

```
PlannerPulse/
│
├── app.py                   # Flask application — all routes
├── main.py                  # Newsletter generation orchestrator
│
├── # LLM integration
├── llm_client.py            # Elysia client + OpenAI-compatible shim (handles OAuth2)
│
├── # Editorial pipeline
├── classifier.py            # TSNN relevance classifier (Elysia gpt-5-mini, 0-100)
├── tsnn_generator.py        # TSNN draft generator (Elysia gpt-4o, structured JSON)
├── ingestion_pipeline.py    # Full pipeline: fetch → dedup → classify → draft
├── newsdata_fetcher.py      # NewsData.io API integration
├── scheduler.py             # APScheduler — 6 AM / 12 PM / 6 PM ET
│
├── # Newsletter generation
├── scraper.py               # RSS feed scraper
├── summarizer.py            # Elysia article summarisation + LLM client init
├── builder.py               # HTML / Markdown / text builder
├── deduplicator.py          # Article deduplication
├── sponsor_manager.py       # Sponsor rotation
│
├── # Data layer
├── models.py                # SQLAlchemy models (incl. IngestedArticle, Draft, EditorialReview)
├── database.py              # Database managers (incl. DraftManager)
│
├── templates/
│   ├── base_template.html   # Newsletter HTML (Informa Connect brand)
│   ├── preview.html         # Newsletter dashboard
│   ├── editorial.html       # Editorial review queue & draft detail
│   ├── analytics.html       # Analytics dashboard
│   ├── digest.html          # Daily editorial digest
│   └── login.html           # Auth page
│
├── static/style.css         # Informa Connect design system
├── config.json              # Sources, sponsors, thresholds, topic taxonomy
└── output/                  # Generated newsletter files
```

---

## Database Schema

| Table | Purpose |
|---|---|
| `ingested_articles` | Every fetched article with relevance score, topic tags, and processing status |
| `drafts` | AI-generated article drafts with full content, quality scores, and editorial status |
| `editorial_reviews` | Audit trail of every approve / reject / edit / regenerate action |
| `articles` | Newsletter-pipeline article history |
| `newsletters` | Generated newsletter archive |
| `sponsors` | Sponsor rotation data |
| `rss_sources` | Configured feed sources |

---

## API Reference

### Newsletter
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Newsletter dashboard |
| `POST` | `/generate` | Generate new newsletter |
| `GET` | `/preview` | Preview latest newsletter HTML |
| `GET` | `/output/<file>` | Serve newsletter file |

### Editorial Pipeline
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/editorial` | Editorial review queue *(auth)* |
| `GET` | `/api/editorial/drafts` | List drafts (`?status=all/draft/approved/rejected`) |
| `GET` | `/api/editorial/draft/<id>` | Full draft detail |
| `POST` | `/api/editorial/approve/<id>` | Approve draft |
| `POST` | `/api/editorial/reject/<id>` | Reject with reason |
| `POST` | `/api/editorial/edit/<id>` | Save inline edits |
| `POST` | `/api/editorial/regenerate/<id>` | Regenerate with instructions |
| `POST` | `/api/editorial/assist/<id>` | AI editorial quality feedback |
| `GET` | `/api/editorial/export/<id>/<fmt>` | Export as `html` / `markdown` / `text` |
| `POST` | `/api/editorial/ingest` | Trigger manual pipeline run *(auth)* |

### Pages
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/analytics` | Analytics dashboard *(auth)* |
| `GET` | `/digest` | Daily editorial digest *(auth)* |
| `GET/POST` | `/login` | Sign in |
| `GET` | `/logout` | Sign out |

---

## Configuration (`config.json`)

Key settings:

```json
{
  "relevance_threshold": 60,
  "draft_threshold": 75,
  "newsdata_api_key": "",
  "content_settings": { "articles_per_newsletter": 8 }
}
```

- `relevance_threshold: 60` — Articles below this are archived
- `draft_threshold: 75` — Articles at or above this get a full TSNN draft

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Flask 3.1+ |
| Auth | Flask-Login |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI provider | Elysia (Informa internal AI platform) |
| AI auth | OAuth2 client_credentials → JWT bearer |
| AI — classification | Elysia `gpt-5-mini` |
| AI — draft generation | Elysia `gpt-4o` |
| AI — editorial assist | Elysia `gpt-4o` |
| Scheduling | APScheduler 3.x |
| RSS parsing | feedparser |
| Full-text extraction | Trafilatura |
| Charts | Chart.js 4 |
| Frontend | Bootstrap 5 + vanilla JS |

---

## Elysia Integration

PlannerPulse routes every LLM call through Elysia, Informa's internal AI platform. The integration lives in `llm_client.py`, which exposes an OpenAI-compatible shim so the application code in `summarizer.py`, `classifier.py`, `tsnn_generator.py`, and `app.py` reads exactly like the old OpenAI calls (`client.chat.completions.create(model=..., messages=..., ...)`).

Under the hood the shim:

1. Fetches a JWT from the Informa IDP (`idp.dev.ai.informa.com/oauth2/token`) using OAuth2 `client_credentials`, caches it, and refreshes a minute before expiry.
2. POSTs to `{ELYSIA_API_BASE}/v2/ai/chat/completion` with the Bearer token, your `appId`, the flattened prompt, and the chosen model.
3. Translates Elysia's `{question, answer, sources}` response back into OpenAI's `choices[0].message.content` shape so callers don't need to change.
4. When `response_format={"type":"json_object"}` is requested, appends a strict JSON-only instruction to the prompt and trims any code fences from the response before returning it.

### Model mapping

PlannerPulse's old OpenAI model names are translated automatically:

| OpenAI request | Elysia `name_of_model` |
|---|---|
| `gpt-4o` | `gpt-4o` |
| `gpt-4o-mini` | `gpt-5-mini` |
| `gpt-4`, `gpt-4-turbo` | `gpt-4o` |
| `gpt-3.5-turbo` | `gpt-5-mini` |

Override the default with `ELYSIA_DEFAULT_MODEL`. Allowed values match Elysia's enum: `gpt-4o`, `gpt-5`, `gpt-5-mini`, the Claude 3.7 / 4 / 4.5 Sonnet variants, and `DeepSeek-V3-0324`.

### Onboarding

To get the three required values (`ELYSIA_APP_ID`, `ELYSIA_CLIENT_ID`, `ELYSIA_CLIENT_SECRET`), contact the Elysia team inside Informa Connect AI. They issue a registered application identifier plus an OAuth2 client. Until those are filled in, all AI features will log a warning and degrade gracefully — the rest of PlannerPulse keeps running.

### Production cutover

Default config points at the **stage** environment (`api.stage.ai.informa.com` + `idp.dev.ai.informa.com`). To go live, set:

```
ELYSIA_API_BASE=https://api.ai.informa.com
ELYSIA_TOKEN_URL=https://idp.ai.informa.com/oauth2/token
```

(confirm the exact prod hostnames with the Elysia team during prod onboarding) and replace your stage credentials with prod-issued ones.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*PlannerPulse — Built for Informa Connect Meetings & Events Intelligence*
