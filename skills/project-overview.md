# Project Overview

## Purpose

PlannerPulse is an internal editorial-intelligence tool for the meetings/events industry
(Informa Connect). It automates news ingestion, AI relevance classification, TSNN-style draft
generation, and a full editorial review workflow — plus a standalone newsletter generator —
all in one Flask web application.

## Two workflows

### 1. Newsletter Generator
Fetches articles from configured RSS feeds, summarizes them with Elysia (GPT-4o by default),
applies source-diversity balancing (round-robin, max ~2 per outlet), rotates sponsors, and
produces HTML/Markdown/text newsletters ready for Beehiiv/Mailchimp/any HTML email editor.

### 2. TSNN AI Editorial Assistant
Monitors industry sources, scores every article 0–100 for TSNN relevance, generates
publication-ready first drafts in TSNN's editorial voice, and presents them in a review
dashboard with approve / reject / edit / regenerate / export / AI-feedback actions.

## Key behaviors

- **Relevance gate:** Elysia `gpt-5-mini` scores articles 0–100 against the TSNN topic
  taxonomy; only **75+** proceed to draft generation.
- **Draft structure:** `gpt-4o` produces a data-forward headline, news lede, structured body
  (`Zooming out:`, `By the numbers:`, `Bottom line:`), a *Why This Matters* section, and 3–5
  takeaways with inline citations, plus 2 alternative headlines.
- **AI editorial feedback:** drafts can be sent back to GPT-4o for a structured quality review.
- **Dedup:** URL-based; already-seen articles skipped, previously-unclassified ones picked up.
- **Automation:** APScheduler runs the pipeline at 6 AM / 12 PM / 6 PM ET; manual "Run
  Pipeline" trigger with a live log.

## App surfaces (routes)

| URL | Purpose | Auth |
|-----|---------|------|
| `/` | Newsletter dashboard | — |
| `/editorial` | Editorial review queue | login |
| `/analytics` | Analytics (Chart.js) | login |
| `/digest` | Daily editorial digest | login |
| `/login` | Auth page | — |

## Who uses it

Informa Connect editorial team (TSNN newsroom) and newsletter operators.

## Status

Python 3.11+, Flask 3.1+, SQLite (dev) / PostgreSQL (prod). Currently points at the Elysia
**stage** stack by default; switch to prod hosts when prod credentials are issued. Originated
on Replit (`.replit`, `replit.md` present).
