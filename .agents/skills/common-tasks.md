# Common Tasks

## Install

```bash
uv sync            # preferred (uv.lock present)
# or: pip install -e .
```

## Configure

Create `.env` (see [technology-stack.md](technology-stack.md) for the full list). Minimum:

```
ELYSIA_APP_ID=...
ELYSIA_CLIENT_ID=...
ELYSIA_CLIENT_SECRET=...
DATABASE_URL=sqlite:///planner_pulse.db
ADMIN_EMAIL=admin@plannerpulse.com
ADMIN_PASSWORD=changeme
SECRET_KEY=change-in-production
FLASK_PORT=5002
```

## Initialize the database

```bash
DATABASE_URL=sqlite:///planner_pulse.db python models.py
```

## Run the app

```bash
DATABASE_URL=sqlite:///planner_pulse.db FLASK_PORT=5002 python app.py
```

Then open:
- `http://localhost:5002/` — newsletter dashboard
- `http://localhost:5002/editorial` — editorial queue (login)
- `http://localhost:5002/analytics` — analytics (login)
- `http://localhost:5002/digest` — daily digest (login)

## Trigger the editorial pipeline

- **Automatic:** APScheduler fires at 6 AM / 12 PM / 6 PM ET while `app.py` runs.
- **Manual:** the "Run Pipeline" button in the Editorial Queue (live log), which invokes
  `ingestion_pipeline.py` (fetch → dedup → classify → draft).

## Generate a newsletter

Run the newsletter orchestrator (`main.py`) — scrapes RSS, summarizes via Elysia, builds
HTML/Markdown/text into `output/`.

## Add or change RSS sources / sponsors / thresholds

Edit `config.json` (`sources`, `sponsors`, `max_articles_per_feed`, output formats, relevance
threshold, taxonomy). No code change needed.

## Add a NewsData.io source

Set `NEWSDATA_API_KEY` in `.env`; `newsdata_fetcher.py` then augments RSS with licensed sources.

## Switch Elysia stage → prod

Set `ELYSIA_API_BASE` / `ELYSIA_TOKEN_URL` to the prod hosts (`api.ai.informa.com` /
`idp.ai.informa.com`) once prod credentials are issued.

## Add a DB field

Update the model in `models.py`, then re-run the DB init (`python models.py`) / migrate.

## Add an editorial route

Add the route in `app.py`, protect with `login_required`, and render a `templates/*.html`
view.
