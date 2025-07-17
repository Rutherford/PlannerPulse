#!/usr/bin/env python3
"""
Test version of the Flask app without OpenAI dependency
"""

import json
import logging
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

# Mock functions to replace OpenAI functionality
def mock_summarize_article(article):
    """Mock article summarization"""
    return {
        'summary': f"This is a mock summary for: {article.get('title', 'Unknown Article')}. The article discusses important developments in the meeting industry that planners should be aware of.",
        'takeaway': "Key insight for meeting planners from this article."
    }

def mock_generate_subject_line(summaries, newsletter_title):
    """Mock subject line generation"""
    return f"{newsletter_title} - Latest Industry Updates • {datetime.now().strftime('%B %d, %Y')}"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'test-secret-key'

def load_config():
    """Load configuration from config.json"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        logger.info("Configuration loaded successfully")
        return config
    except FileNotFoundError:
        logger.error("config.json not found")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config.json: {e}")
        raise

@app.route('/')
def index():
    """Main dashboard"""
    try:
        config = load_config()
        
        # Mock statistics
        stats = {
            'total_processed': 125,
            'total_sponsors': len(config.get("sponsors", [])),
            'current_sponsor': config.get("sponsors", [{}])[0] if config.get("sponsors") else {},
            'rss_sources': len(config.get("sources", [])),
            'articles_today': 8,
            'newsletters_today': 1,
            'total_newsletters': 15
        }
        
        # Check if recent newsletter exists
        recent_newsletter = None
        if os.path.exists('output/newsletter.html'):
            stat = os.stat('output/newsletter.html')
            recent_newsletter = {
                'exists': True,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            }
        
        return render_template('preview.html', 
                             config=config, 
                             stats=stats, 
                             recent_newsletter=recent_newsletter)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash(f"Error loading dashboard: {e}", 'error')
        return render_template('preview.html', config={}, stats={}, recent_newsletter=None)

@app.route('/generate', methods=['POST'])
def generate_newsletter():
    """Generate test newsletter"""
    try:
        # Import scraper for RSS functionality
        from scraper import fetch_articles
        from builder import build_newsletter
        
        config = load_config()
        
        # Fetch articles
        logger.info("Fetching articles from RSS sources")
        raw_articles = fetch_articles(config["sources"], max_per_feed=2)  # Limit for testing
        logger.info(f"Fetched {len(raw_articles)} raw articles")
        
        if not raw_articles:
            flash("No articles found from RSS sources", 'warning')
            return redirect(url_for('index'))
        
        # Mock summarization
        summaries = []
        for article in raw_articles[:5]:  # Limit to 5 articles for testing
            summary_data = mock_summarize_article(article)
            summaries.append({
                **article,
                'summary': summary_data.get('summary', ''),
                'takeaway': summary_data.get('takeaway', '')
            })
        
        # Generate subject line
        subject_line = mock_generate_subject_line(summaries, config["newsletter_title"])
        
        # Get current sponsor
        current_sponsor = config.get("sponsors", [{}])[0] if config.get("sponsors") else {}
        
        # Build newsletter
        newsletter_data = {
            'title': config["newsletter_title"],
            'subject_line': subject_line,
            'stories': summaries,
            'sponsor': current_sponsor,
            'generated_at': datetime.now().isoformat()
        }
        
        success, _, _, _ = build_newsletter(newsletter_data, config)

        if success:
            flash('Test newsletter generated successfully!', 'success')
            logger.info("Test newsletter generation completed successfully")
        else:
            flash('Newsletter generation failed.', 'error')
            
    except Exception as e:
        logger.error(f"Error generating newsletter: {e}")
        flash(f'Error generating newsletter: {e}', 'error')
    
    return redirect(url_for('index'))

@app.route('/preview')
def preview_newsletter():
    """Preview generated newsletter"""
    try:
        if os.path.exists('output/newsletter.html'):
            with open('output/newsletter.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content
        else:
            return "<h1>No newsletter found</h1><p>Generate a newsletter first.</p>"
    except Exception as e:
        logger.error(f"Error loading newsletter preview: {e}")
        return f"<h1>Error</h1><p>Failed to load newsletter: {e}</p>"

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    try:
        config = load_config()
        
        stats = {
            'total_processed': 125,
            'total_sponsors': len(config.get("sponsors", [])),
            'current_sponsor': config.get("sponsors", [{}])[0] if config.get("sponsors") else {},
            'rss_sources': len(config.get("sources", [])),
            'last_generated': None,
            'articles_today': 8,
            'newsletters_today': 1,
            'total_newsletters': 15
        }
        
        if os.path.exists('output/newsletter.html'):
            stat = os.stat('output/newsletter.html')
            stats['last_generated'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    print("🚀 Starting PlannerPulse Test Server...")
    print("📧 Note: This is a test version without OpenAI integration")
    print("🌐 Access the dashboard at: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
