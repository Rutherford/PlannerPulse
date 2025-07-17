"""
RSS Feed Scraper for Meeting Industry Sources
Fetches articles from RSS feeds with fallback handling
"""

import feedparser
import requests
import trafilatura
import logging
from typing import List, Dict
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

def fetch_articles(rss_urls: List[str], max_per_feed: int = 5) -> List[Dict]:
    """
    Fetch articles from RSS feeds
    
    Args:
        rss_urls: List of RSS feed URLs
        max_per_feed: Maximum articles to fetch per feed
    
    Returns:
        List of article dictionaries with title, link, summary, source
    """
    articles = []
    
    for url in rss_urls:
        try:
            logger.info(f"Fetching from RSS feed: {url}")
            feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.warning(f"RSS feed may have issues: {url}")
            
            feed_title = getattr(feed.feed, 'title', urlparse(url).netloc)
            logger.info(f"Found {len(feed.entries)} entries in {feed_title}")
            
            for entry in feed.entries[:max_per_feed]:
                try:
                    article = extract_article_data(entry, feed_title)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error processing entry from {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to fetch RSS feed {url}: {e}")
            continue
    
    logger.info(f"Total articles fetched: {len(articles)}")
    return articles

def extract_article_data(entry, source_name: str) -> Dict:
    """
    Extract relevant data from RSS entry
    
    Args:
        entry: RSS feed entry
        source_name: Name of the RSS source
    
    Returns:
        Dictionary with article data
    """
    try:
        # Basic article data
        article = {
            'title': getattr(entry, 'title', 'No Title'),
            'link': getattr(entry, 'link', ''),
            'source': source_name,
            'published': getattr(entry, 'published', ''),
        }
        
        # Extract summary/description
        summary = ''
        if hasattr(entry, 'summary'):
            summary = entry.summary
        elif hasattr(entry, 'description'):
            summary = entry.description
        elif hasattr(entry, 'content'):
            if isinstance(entry.content, list) and entry.content:
                summary = entry.content[0].value
        
        # Clean HTML from summary
        if summary:
            # Remove HTML tags for cleaner text
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = summary.strip()
        
        article['summary'] = summary
        
        # Try to get full content if summary is short
        if len(summary) < 100 and article['link']:
            try:
                full_content = get_full_article_content(article['link'])
                if full_content and len(full_content) > len(summary):
                    article['full_content'] = full_content
            except Exception as e:
                logger.debug(f"Could not fetch full content for {article['link']}: {e}")
        
        return article
        
    except Exception as e:
        logger.error(f"Error extracting article data: {e}")
        return None

def get_full_article_content(url: str) -> str:
    """
    Fetch full article content using trafilatura
    
    Args:
        url: Article URL
    
    Returns:
        Extracted text content
    """
    try:
        logger.debug(f"Fetching full content from: {url}")
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            return text if text else ""
        return ""
    except Exception as e:
        logger.debug(f"Failed to extract full content from {url}: {e}")
        return ""

def validate_rss_url(url: str) -> bool:
    """
    Validate if RSS URL is accessible
    
    Args:
        url: RSS feed URL
    
    Returns:
        True if valid and accessible
    """
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

# Default RSS sources for meeting industry
DEFAULT_SOURCES = [
    "https://www.meetingstoday.com/rss.xml",
    "https://www.bizbash.com/rss.xml", 
    "https://www.tsnn.com/news/rss.xml",
    "https://www.meetings-conventions.com/rss.xml",
    "https://www.eventmanagerblog.com/feed"
]

if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)
    articles = fetch_articles(DEFAULT_SOURCES[:2], max_per_feed=3)
    
    print(f"\nFetched {len(articles)} articles:")
    for i, article in enumerate(articles):
        print(f"\n{i+1}. {article['title']}")
        print(f"   Source: {article['source']}")
        print(f"   Link: {article['link']}")
        print(f"   Summary: {article['summary'][:100]}...")
