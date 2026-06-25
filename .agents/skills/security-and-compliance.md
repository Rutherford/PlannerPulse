# Security & Compliance

## Secrets

- Elysia credentials (`ELYSIA_CLIENT_ID`/`ELYSIA_CLIENT_SECRET`/`ELYSIA_APP_ID`), DB URL,
  `NEWSDATA_API_KEY`, `SECRET_KEY`, and admin credentials all come from `.env`.
- **Never commit `.env`** or `SECRET_KEY`/admin passwords. The README ships example values
  (`ADMIN_PASSWORD=changeme`, `SECRET_KEY=change-in-production`) — change them for any real
  deployment.

## Authentication & access control

- Editorial, analytics, and digest routes are protected by Flask-Login. Keep new
  draft/analytics routes `login_required`.
- Set a strong, unique `SECRET_KEY` in production (Flask session signing).
- Admin login is a single configured account via env vars — treat those credentials carefully.

## AI / content governance

- All model calls go through **Elysia** (Informa's governed AI platform) with OAuth2 — this is
  the sanctioned path; don't route to external LLM providers directly.
- **Human-in-the-loop:** AI output is a draft. The approve/reject workflow and the
  `editorial_reviews` audit trail ensure a person signs off before publication. Don't
  auto-publish AI content.
- **Provenance:** drafts carry inline source citations; preserve attribution so editors can
  verify factual claims (mitigates hallucination risk).

## Content sourcing

- Articles come from third-party RSS feeds and (optionally) NewsData.io. Respect each source's
  terms; the tool ingests for internal editorial review, and human editors decide what to
  publish/rewrite.

## Stage vs prod separation

- Defaults target the Elysia **stage/dev** stack. Don't point prod editorial traffic at stage,
  or mix stage credentials with prod endpoints.

## Data store

- SQLite DB file (`planner_pulse.db`) and `newsletter.log` live in the repo working tree —
  ensure they're gitignored and not shipped with real data.

## TODO / to verify

- `TODO`: Confirm `.gitignore` excludes `.env`, `planner_pulse.db`, `newsletter.log`, and
  `output/` so secrets and content aren't committed.
- `TODO`: Confirm whether any committed DB file contains real ingested content that should be
  purged before sharing.
