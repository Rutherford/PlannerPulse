"""
Article deduplication system to prevent reposting content
"""

import json
import logging
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Set
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class ArticleDeduplicator:
    """Manages article deduplication using URL tracking and content hashing"""
    
    def __init__(self, history_file: str = "data/article_history.json"):
        self.history_file = history_file
        self.processed_urls: Set[str] = set()
        self.processed_hashes: Set[str] = set()
        self.article_metadata: Dict[str, Dict] = {}
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        
        # Load existing history
        self.load_history()
    
    def load_history(self):
        """Load article history from JSON file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.processed_urls = set(data.get('processed_urls', []))
                self.processed_hashes = set(data.get('processed_hashes', []))
                self.article_metadata = data.get('article_metadata', {})
                
                logger.info(f"Loaded {len(self.processed_urls)} processed URLs from history")
            else:
                logger.info("No existing article history found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load article history: {e}")
            # Continue with empty sets
    
    def save_history(self):
        """Save article history to JSON file"""
        try:
            data = {
                'processed_urls': list(self.processed_urls),
                'processed_hashes': list(self.processed_hashes),
                'article_metadata': self.article_metadata,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Article history saved")
        except Exception as e:
            logger.error(f"Failed to save article history: {e}")
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize URL to catch duplicate articles with different parameters
        
        Args:
            url: Original URL
        
        Returns:
            Normalized URL string
        """
        try:
            parsed = urlparse(url.lower().strip())
            
            # Remove common tracking parameters
            tracking_params = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'fbclid', 'gclid', 'ref', 'source', 'campaign'
            }
            
            # Parse query parameters
            query_params = parse_qs(parsed.query)
            
            # Filter out tracking parameters
            clean_params = {
                k: v for k, v in query_params.items() 
                if k.lower() not in tracking_params
            }
            
            # Rebuild query string
            if clean_params:
                from urllib.parse import urlencode
                clean_query = urlencode(clean_params, doseq=True)
                normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{clean_query}"
            else:
                normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # Remove trailing slash
            normalized = normalized.rstrip('/')
            
            return normalized
            
        except Exception as e:
            logger.warning(f"Failed to normalize URL {url}: {e}")
            return url.lower().strip()
    
    def generate_content_hash(self, article: Dict) -> str:
        """
        Generate hash for article content to detect duplicates with different URLs
        
        Args:
            article: Article dictionary
        
        Returns:
            MD5 hash of normalized content
        """
        try:
            # Combine title and summary for content hash
            title = article.get('title', '').strip().lower()
            summary = article.get('summary', '').strip().lower()
            
            # Remove extra whitespace and punctuation for better matching
            import re
            title = re.sub(r'\s+', ' ', title)
            summary = re.sub(r'\s+', ' ', summary)
            
            # Create content string
            content = f"{title}|{summary}"
            
            # Generate hash
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            return content_hash
            
        except Exception as e:
            logger.warning(f"Failed to generate content hash: {e}")
            return ""
    
    def is_duplicate(self, article: Dict) -> bool:
        """
        Check if article is a duplicate
        
        Args:
            article: Article dictionary with 'link', 'title', 'summary'
        
        Returns:
            True if article is a duplicate
        """
        try:
            # Check URL
            if 'link' in article:
                normalized_url = self.normalize_url(article['link'])
                if normalized_url in self.processed_urls:
                    logger.debug(f"Duplicate URL found: {article.get('title', 'Unknown')}")
                    return True
            
            # Check content hash
            content_hash = self.generate_content_hash(article)
            if content_hash and content_hash in self.processed_hashes:
                logger.debug(f"Duplicate content found: {article.get('title', 'Unknown')}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return False
    
    def filter_new_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Filter out duplicate articles from the list
        
        Args:
            articles: List of article dictionaries
        
        Returns:
            List of new (non-duplicate) articles
        """
        new_articles = []
        duplicates_found = 0
        
        for article in articles:
            if not self.is_duplicate(article):
                new_articles.append(article)
            else:
                duplicates_found += 1
        
        logger.info(f"Filtered out {duplicates_found} duplicate articles")
        logger.info(f"Found {len(new_articles)} new articles")
        
        return new_articles
    
    def mark_articles_processed(self, articles_or_urls: List):
        """
        Mark articles as processed to prevent future duplication
        
        Args:
            articles_or_urls: List of article dictionaries or URLs
        """
        try:
            for item in articles_or_urls:
                if isinstance(item, dict):
                    # Article dictionary
                    article = item
                    if 'link' in article:
                        normalized_url = self.normalize_url(article['link'])
                        self.processed_urls.add(normalized_url)
                    
                    content_hash = self.generate_content_hash(article)
                    if content_hash:
                        self.processed_hashes.add(content_hash)
                    
                    # Store metadata
                    if 'link' in article:
                        self.article_metadata[normalized_url] = {
                            'title': article.get('title', ''),
                            'processed_at': datetime.now().isoformat(),
                            'source': article.get('source', '')
                        }
                
                elif isinstance(item, str):
                    # URL string
                    normalized_url = self.normalize_url(item)
                    self.processed_urls.add(normalized_url)
                    
                    self.article_metadata[normalized_url] = {
                        'processed_at': datetime.now().isoformat(),
                        'source': 'manual'
                    }
            
            # Save updated history
            self.save_history()
            
            logger.info(f"Marked {len(articles_or_urls)} articles as processed")
            
        except Exception as e:
            logger.error(f"Failed to mark articles as processed: {e}")
    
    def get_stats(self) -> Dict:
        """Get deduplication statistics"""
        return {
            'total_processed_urls': len(self.processed_urls),
            'total_processed_hashes': len(self.processed_hashes),
            'total_articles_tracked': len(self.article_metadata)
        }
    
    def reset_history(self):
        """Reset article history (for testing/maintenance)"""
        try:
            self.processed_urls.clear()
            self.processed_hashes.clear()
            self.article_metadata.clear()
            
            # Remove history file
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
            
            logger.info("Article history reset")
            
        except Exception as e:
            logger.error(f"Failed to reset history: {e}")
    
    def cleanup_old_entries(self, days_to_keep: int = 90):
        """
        Remove old entries to prevent history file from growing too large
        
        Args:
            days_to_keep: Number of days to keep in history
        """
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            urls_to_remove = []
            for url, metadata in self.article_metadata.items():
                try:
                    processed_at = datetime.fromisoformat(metadata.get('processed_at', ''))
                    if processed_at < cutoff_date:
                        urls_to_remove.append(url)
                except ValueError:
                    # Invalid date format, remove old entry
                    urls_to_remove.append(url)
            
            # Remove old entries
            for url in urls_to_remove:
                self.processed_urls.discard(url)
                self.article_metadata.pop(url, None)
            
            # Note: We keep content hashes as they're small and provide good duplicate detection
            
            if urls_to_remove:
                self.save_history()
                logger.info(f"Cleaned up {len(urls_to_remove)} old entries from history")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old entries: {e}")

if __name__ == "__main__":
    # Test the deduplicator
    logging.basicConfig(level=logging.INFO)
    
    dedup = ArticleDeduplicator("data/test_history.json")
    
    # Test articles
    test_articles = [
        {
            'title': 'Test Article 1',
            'link': 'https://example.com/article1',
            'summary': 'This is a test article summary.'
        },
        {
            'title': 'Test Article 2', 
            'link': 'https://example.com/article2?utm_source=test',
            'summary': 'This is another test article.'
        },
        {
            'title': 'Test Article 1',  # Duplicate title/content
            'link': 'https://different.com/article',
            'summary': 'This is a test article summary.'
        }
    ]
    
    print("Testing deduplication...")
    
    # First run - all should be new
    new_articles = dedup.filter_new_articles(test_articles)
    print(f"First run: {len(new_articles)} new articles")
    
    # Mark as processed
    dedup.mark_articles_processed(new_articles)
    
    # Second run - should find duplicates
    new_articles = dedup.filter_new_articles(test_articles)
    print(f"Second run: {len(new_articles)} new articles")
    
    # Stats
    stats = dedup.get_stats()
    print(f"Stats: {stats}")
