# Technology Stack

## Language & runtime

- **Python ≥ 3.11**. Dependency management via **uv** (`uv.lock`, `pyproject.toml`); also
  `pip install -e .`. Project metadata name is `repl-nix-workspace` (Replit origin).

## Dependencies (`pyproject.toml`)

| Package | Role |
|---------|------|
| `flask`, `flask-login`, `flask-sqlalchemy` | Web app, session auth, ORM integration |
| `sqlalchemy` | ORM / data layer (`models.py`, `database.py`) |
| `psycopg2-binary` | PostgreSQL driver (production DB) |
| `jinja2` | HTML/Markdown/text templating |
| `apscheduler` | Scheduled pipeline runs |
| `feedparser`, `beautifulsoup4`, `trafilatura` | RSS parsing + article extraction |
| `requests` | HTTP (Elysia, NewsData.io, scraping) |
| `python-dotenv` | Load `.env` |

## LLM platform — Elysia (Informa internal AI)

- All model calls go through **Elysia** (`api.stage.ai.informa.com`) via an OpenAI-compatible
  shim in `llm_client.py`.
- Auth: **OAuth2 client_credentials** against the Informa IDP.
- Models referenced: `gpt-5-mini` (relevance, cheap), `gpt-4o` (drafts/feedback, default).
  Elysia can also route `gpt-5`, `claude-*`, `DeepSeek-V3-0324`; provider `azure`|`aws`.

## Data stores

- **SQLite** for local dev (`planner_pulse.db`), **PostgreSQL** for production — selected by
  `DATABASE_URL`.

## Frontend

- Server-rendered Jinja2 templates in `templates/`, Informa Connect design system in
  `static/style.css`, Chart.js on the analytics dashboard.

## Key environment variables

| Var | Purpose |
|-----|---------|
| `ELYSIA_APP_ID`, `ELYSIA_CLIENT_ID`, `ELYSIA_CLIENT_SECRET` | Required Elysia credentials |
| `ELYSIA_API_BASE`, `ELYSIA_TOKEN_URL`, `ELYSIA_SCOPE` | Elysia stack pointers (stage by default) |
| `ELYSIA_DEFAULT_MODEL`, `ELYSIA_DEFAULT_PROVIDER` | Model/provider defaults |
| `DATABASE_URL` | DB connection (SQLite/Postgres) |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_NAME` | Editorial login |
| `NEWSDATA_API_KEY` | Optional NewsData.io source |
| `SECRET_KEY`, `FLASK_PORT` | Flask session key, port (default 5002) |

## Run

```bash
uv sync                                   # or: pip install -e .
DATABASE_URL=sqlite:///planner_pulse.db python models.py   # init DB
DATABASE_URL=sqlite:///planner_pulse.db FLASK_PORT=5002 python app.py
```
