"""
AI-powered article summarization and subject line generation using OpenAI GPT-4o
"""

import os
import logging
import json
from typing import Dict, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY environment variable is required")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

def summarize_article(article: Dict) -> Optional[str]:
    """
    Summarize an article for newsletter inclusion using GPT-4o
    
    Args:
        article: Dictionary containing article data (title, summary, full_content, etc.)
    
    Returns:
        Formatted summary string or None if failed
    """
    try:
        # Prepare content for summarization
        content_to_summarize = article.get('summary', '')
        
        # Use full content if available and summary is short
        if article.get('full_content') and len(content_to_summarize) < 200:
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
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert content curator for meeting and event industry professionals. You specialize in creating engaging, informative newsletter content."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
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
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert email marketing specialist for the meetings and events industry."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=100
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

        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
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
