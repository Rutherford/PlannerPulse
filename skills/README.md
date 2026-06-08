# Skills — PlannerPulse

Knowledge base for humans and AI agents working in this repo.

## What this project is

**PlannerPulse** is an internal **AI-powered newsletter generator + editorial assistant for
the meetings & events industry**, built for Informa Connect as a single Flask web app. It
runs two parallel workflows:

1. **Newsletter Generator** — scrapes industry RSS feeds, summarizes with Elysia, balances
   sources, and outputs HTML/Markdown/text newsletters.
2. **TSNN AI Editorial Assistant** — ingests articles, scores TSNN relevance (0–100),
   generates publication-ready drafts in TSNN's voice, and serves an editorial review
   dashboard (approve/reject/regenerate/export/AI-feedback).

All LLM calls route through **Elysia**, Informa's internal AI platform
(`api.stage.ai.informa.com`), via OAuth2 client_credentials.

## How to use these docs

| File | When you want to… |
|------|-------------------|
| [project-overview.md](project-overview.md) | Understand the two workflows and scope |
| [architecture.md](architecture.md) | See the pipeline and Flask app layout |
| [technology-stack.md](technology-stack.md) | Know the stack and deps |
| [coding-standards.md](coding-standards.md) | Match conventions |
| [best-practices.md](best-practices.md) | Follow the safe patterns |
| [domain-knowledge.md](domain-knowledge.md) | TSNN relevance, scoring, editorial workflow |
| [glossary.md](glossary.md) | Decode Elysia/TSNN/editorial terms |
| [common-tasks.md](common-tasks.md) | Install, init DB, run, trigger pipeline |
| [api-and-integrations.md](api-and-integrations.md) | Elysia, NewsData.io, RSS, DB |
| [security-and-compliance.md](security-and-compliance.md) | Secrets, auth, content provenance |
| [testing-and-quality.md](testing-and-quality.md) | Current (limited) test posture |
| [troubleshooting.md](troubleshooting.md) | Auth, DB, scheduler, LLM issues |
| [contributing.md](contributing.md) | Make changes safely |

## Quick orientation

- **Flask app + all routes:** `app.py` (port via `FLASK_PORT`, default 5002).
- **LLM gateway:** `llm_client.py` (Elysia client + OpenAI-compatible shim, OAuth2).
- **Editorial pipeline:** `ingestion_pipeline.py` → `classifier.py` (gpt-5-mini) → `tsnn_generator.py` (gpt-4o).
- **Newsletter pipeline:** `scraper.py` → `summarizer.py` → `deduplicator.py` → `sponsor_manager.py` → `builder.py`, orchestrated by `main.py`.
- **Scheduling:** `scheduler.py` (APScheduler, 6 AM / 12 PM / 6 PM ET).
- **Data:** `models.py` (SQLAlchemy) + `database.py` (managers); `config.json` (sources, sponsors, taxonomy).
