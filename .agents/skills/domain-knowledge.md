# Domain Knowledge — TSNN Editorial & Meetings-Industry Newsletter

## The two products

- **TSNN** (Trade Show News Network): the editorial brand the AI assistant writes for. Drafts
  must match TSNN's voice and topic focus.
- **Planner Pulse newsletter**: a curated digest for meeting/event planners assembled from
  industry RSS sources.

## TSNN topic taxonomy (relevance scoring)

Articles are scored 0–100 against TSNN's topics (defined in `config.json` / classifier prompt):

- Trade Show Operations
- Venues & Convention Centers
- Event Technology
- Industry Organisations
- Major Organisers
- M&A (mergers & acquisitions)
- Market Data

**Only articles scoring 75+** advance from classification (`gpt-5-mini`) to draft generation
(`gpt-4o`).

## TSNN draft structure

A generated draft (from `tsnn_generator.py`) follows the TSNN AI Editorial Assistant PRD:

- **Data-forward headline** (+ 2 alternative headline angles)
- **News lede**
- **Structured body** with labeled sections: `Zooming out:`, `By the numbers:`, `Bottom line:`
- **Why This Matters to Event Professionals** section
- **3–5 key takeaway bullets** with inline source citations

## Editorial workflow & states

Articles/drafts move through statuses tracked in the DB:

- `ingested_articles`: fetched → scored → (if 75+) drafted.
- `drafts`: Pending → Approved / Rejected (with categorized reason: Not relevant, Inaccurate,
  Tone mismatch, Already covered, etc.).
- Every approve/reject/edit/regenerate is recorded in `editorial_reviews` (audit trail).
- **AI Feedback** returns a structured review: Overall score, TSNN Voice score, Strengths,
  Issues (with severity), Missing Context, Suggested Improvements.

## Newsletter generation rules

- **Source diversity:** round-robin interleaving, **max ~2 articles per outlet**, to avoid one
  publication dominating.
- **Summarization:** Elysia (GPT-4o default) summarizes each article and extracts key
  takeaways; an AI-generated subject line is produced.
- **Sponsors:** CVB/DMO (Convention & Visitors Bureau / Destination Marketing Organization)
  sponsor messages rotate (`sponsor_manager.py`, configured in `config.json`).
- **Output:** professional HTML (Informa Connect brand — Georgia serif masthead), plus
  Markdown and text, ready for Beehiiv/Mailchimp.

## Scheduling

APScheduler runs the editorial pipeline at **6:00 AM, 12:00 PM, 6:00 PM ET** while the app is
running. The `/digest` page is the editorial morning briefing of pending drafts.

## Sources

RSS feeds (7+ meetings/events publications, e.g. MeetingsToday, BizBash, TSNN, Skift Meetings,
Event Industry News) listed in `config.json`. Optional NewsData.io adds licensed sources when
`NEWSDATA_API_KEY` is set.
