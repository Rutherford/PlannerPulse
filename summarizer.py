"""
AI-powered article summarization and subject line generation.

LLM provider: Elysia (Informa's internal AI platform), accessed via the
OpenAI-compatible shim in ``llm_client``. The legacy variable name
``openai_client`` is kept so callers across the codebase keep working.
"""

import os
import logging
import json
from typing import Dict, List, Optional

import llm_client

logger = logging.getLogger(__name__)

# Configuration constants
MIN_CONTENT_LENGTH_FOR_SUMMARY = 200
MAX_TOKENS_SUMMARY = 300
MAX_TOKENS_SUBJECT_LINE = 100
LLM_MODEL = "gpt-4o"
LLM_TEMPERATURE_SUMMARY = 0.7
LLM_TEMPERATURE_SUBJECT = 0.8  # kept for parity; Elysia controls temperature internally
# Backward-compatible aliases (a few call sites still reference these names)
OPENAI_MODEL = LLM_MODEL
OPENAI_TEMPERATURE_SUMMARY = LLM_TEMPERATURE_SUMMARY
OPENAI_TEMPERATURE_SUBJECT = LLM_TEMPERATURE_SUBJECT

# Global LLM client. Same name as before so importers don't break.
openai_client = None


def initialize_openai_client(api_key=None):
    """Initialise the Elysia-backed LLM client.

    The ``api_key`` argument is accepted for backwards compatibility with the
    old OpenAI-based code path but is ignored — Elysia uses an OAuth2
    client_credentials grant configured via ``ELYSIA_*`` env vars.
    """
    global openai_client

    if api_key:
        logger.info(
            "initialize_openai_client(api_key=...) was called, but the new "
            "Elysia backend authenticates via ELYSIA_CLIENT_ID/SECRET. "
            "The supplied api_key is ignored."
        )

    client = llm_client.get_default_client(refresh=True)
    if client is None:
        openai_client = None
        return False

    openai_client = client
    logger.info("Elysia LLM client initialised successfully")
    return True


def test_api_connection(api_key=None):
    """Smoke-test the LLM connection. Returns (ok, detail)."""
    if api_key:
        logger.info("test_api_connection ignores legacy api_key argument under Elysia backend.")
    return llm_client.test_connection()


# Try to initialize on import
if not initialize_openai_client():
    logger.warning(
        "Elysia LLM client not initialised — set ELYSIA_APP_ID, "
        "ELYSIA_CLIENT_ID and ELYSIA_CLIENT_SECRET to enable LLM features."
    )

def summarize_article(article: Dict) -> Optional[str]:
    """
    Summarize an article for newsletter inclusion using GPT-4o
    
    Args:
        article: Dictionary containing article data (title, summary, full_content, etc.)
    
    Returns:
        Formatted summary string or None if failed
    """
    global openai_client
    
    # Check if client is initialized
    if not openai_client:
        if not initialize_openai_client():
            logger.error("Cannot summarize article: OpenAI client not initialized")
            return None
    
    try:
        # Prepare content for summarization
        content_to_summarize = article.get('summary', '')
        
        # Use full content if available and summary is short
        if article.get('full_content') and len(content_to_summarize) < MIN_CONTENT_LENGTH_FOR_SUMMARY:
            content_to_summarize = article['full_content']
        
        if not content_to_summarize.strip():
            logger.warning(f"No content to summarize for article: {article.get('title', 'Unknown')}")
            return None
        
        # Craft prompt for meeting planner audience
        prompt = f"""
You are writing for a newsletter targeted at meeting planners and event professionals. 

Please summarize this article in a format suitable for a professional newsletter:

**Article Title:** {article.get('title', 'Unknown')}
**Source:** {article.get('source', 'Unknown')}

**Content:**
{content_to_summarize}

**Instructions:**
1. Write a summary in NO MORE THAN 3 SHORT SENTENCES (max 60 words total)
2. AVOID repeating the title or quoting full sentences from the article
3. Focus on NEW information not already in the title
4. Emphasize what's relevant to meeting planners and event professionals
5. Include ONE key takeaway marked with 🔑 (max 15 words)

**Format your response EXACTLY like this:**
[2-3 short sentences summarizing the key points - max 60 words total]
🔑 **Key Takeaway:** [One actionable insight - max 15 words]
"""

        # Call GPT-4o for summarization
        # Using OpenAI GPT-4o model (released May 13, 2024)
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert content curator for meeting and event industry professionals. You specialize in creating engaging, informative newsletter content."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=OPENAI_TEMPERATURE_SUMMARY,
            max_tokens=MAX_TOKENS_SUMMARY
        )
        
        summary_text = response.choices[0].message.content.strip()
        
        if summary_text:
            logger.info(f"Successfully summarized: {article.get('title', 'Unknown')}")
            
            # Parse the summary to extract takeaway
            lines = summary_text.split('\n')
            summary = ""
            takeaway = ""
            
            for line in lines:
                if '🔑' in line or 'Key Takeaway:' in line:
                    # Extract takeaway
                    takeaway = line.replace('🔑', '').replace('**Key Takeaway:**', '').strip()
                    takeaway = takeaway.replace('**', '').strip()
                else:
                    summary += line + " "
            
            # Return structured data
            return {
                'summary': summary.strip(),
                'takeaway': takeaway
            }
        else:
            logger.warning(f"Empty summary returned for: {article.get('title', 'Unknown')}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to summarize article '{article.get('title', 'Unknown')}': {e}")
        return None

def generate_subject_line(summaries: List[Dict], newsletter_title: str) -> str:
    """
    Generate compelling subject line for the newsletter using GPT-4o
    
    Args:
        summaries: List of article summaries
        newsletter_title: Newsletter brand name
    
    Returns:
        Generated subject line
    """
    global openai_client
    
    # Check if client is initialized
    if not openai_client:
        if not initialize_openai_client():
            logger.error("Cannot generate subject line: OpenAI client not initialized")
            # Return a fallback subject line
            from datetime import datetime
            return f"{newsletter_title} - {datetime.now().strftime('%B %d, %Y')}"
    
    try:
        # Extract key topics from summaries
        topics = []
        for summary in summaries[:5]:  # Use first 5 summaries for subject line
            if isinstance(summary, dict):
                topics.append(summary.get('title', ''))
                if 'summary' in summary:
                    topics.append(summary['summary'])
            else:
                topics.append(str(summary))
        
        topics_text = "\n".join(topics)
        
        prompt = f"""
Based on these newsletter stories for meeting planners and event professionals, create a compelling email subject line.

**Newsletter Content Topics:**
{topics_text}

**Requirements:**
1. Maximum 90 characters (aim for 60-80)
2. Include the TOP 2-3 stories in a concise format
3. Use pipe (|) or bullet (•) to separate topics
4. Appeal to meeting planners and event professionals
5. Be specific with numbers, locations, or trends when possible
6. Create urgency without clickbait

**Examples of good subject lines:**
- "Vegas Venue Tax Rises 12% | Hybrid Events Boom | Orlando Expansion"
- "Incentives Are Back • Hotel Rates Jump • $600M in New Venues"
- "AI Tools for Planners | Boston Hotels at 90% | Green Meetings Trend"

Generate ONE subject line that summarizes the top 2-3 stories. Return only the subject line, no explanation.
"""

        # Generate subject line with GPT-4o
        # Using OpenAI GPT-4o model (released May 13, 2024)
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert email marketing specialist for the meetings and events industry."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=OPENAI_TEMPERATURE_SUBJECT,
            max_tokens=MAX_TOKENS_SUBJECT_LINE
        )
        
        subject_line = response.choices[0].message.content.strip()
        
        # Clean up the subject line
        subject_line = subject_line.replace('"', '').replace("'", "").strip()
        
        logger.info(f"Generated subject line: {subject_line}")
        return subject_line
        
    except Exception as e:
        logger.error(f"Failed to generate subject line: {e}")
        # Fallback subject line
        from datetime import datetime
        return f"{newsletter_title} - {datetime.now().strftime('%B %d, %Y')}"

def analyze_content_themes(summaries: List[Dict]) -> Dict:
    """
    Analyze content themes for insights (optional feature)
    
    Args:
        summaries: List of article summaries
    
    Returns:
        Dictionary with theme analysis
    """
    try:
        content_text = "\n\n".join([
            summary.get('summary', '') if isinstance(summary, dict) else str(summary) 
            for summary in summaries
        ])
        
        prompt = f"""
Analyze these meeting industry newsletter stories and identify the main themes:

{content_text}

Return a JSON object with:
1. "primary_themes": List of 3-5 main topics covered
2. "industry_sentiment": "positive", "neutral", or "negative" 
3. "trending_topics": List of 2-3 trending subjects
4. "geographic_focus": List of mentioned locations/regions

Format as valid JSON only.
"""

        if not openai_client:
            initialize_openai_client()
        if not openai_client:
            raise RuntimeError("LLM client not initialised")

        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        analysis = json.loads(response.choices[0].message.content)
        logger.info("Content theme analysis completed")
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze content themes: {e}")
        return {
            "primary_themes": [],
            "industry_sentiment": "neutral",
            "trending_topics": [],
            "geographic_focus": []
        }

if __name__ == "__main__":
    # Test the summarizer
    logging.basicConfig(level=logging.INFO)
    
    test_article = {
        'title': 'Major Hotel Chain Announces New Meeting Spaces',
        'summary': 'Marriott International announced plans to add 500 new meeting rooms across their portfolio by 2025, responding to increased demand for hybrid event capabilities.',
        'source': 'Meetings Today'
    }
    
    summary = summarize_article(test_article)
    if summary:
        print("Generated Summary:")
        print(summary)
        
        subject = generate_subject_line([{'summary': summary}], "Planner Pulse")
        print(f"\nGenerated Subject Line: {subject}")
