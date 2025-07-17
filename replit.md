# Planner Pulse - AI-Powered Newsletter Generator

## Overview

Planner Pulse is an automated newsletter generation system designed specifically for meeting planners and event professionals. The application scrapes RSS feeds from major meeting industry sources, uses OpenAI's GPT-4o to intelligently summarize articles, and generates professional newsletters in multiple formats (HTML, Markdown, and plain text). The system includes sophisticated deduplication, sponsor rotation, and a Flask-based web interface for management and preview.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular, service-oriented architecture with clear separation of concerns:

- **Web Interface Layer**: Flask-based dashboard for management and preview
- **Content Processing Pipeline**: RSS scraping → deduplication → summarization → newsletter building
- **Data Persistence**: JSON-based file storage for article history, sponsor state, and configuration
- **External AI Integration**: OpenAI GPT-4o for content summarization and subject line generation
- **Multi-format Output**: HTML, Markdown, and plain text newsletter generation

## Key Components

### Core Processing Modules

1. **RSS Scraper** (`scraper.py`)
   - Fetches articles from multiple RSS feeds using feedparser
   - Includes fallback content extraction with trafilatura
   - Handles feed parsing errors gracefully

2. **Article Deduplicator** (`deduplicator.py`)
   - Prevents duplicate content using URL tracking and content hashing
   - Maintains persistent history in JSON format
   - Implements both URL-based and content-hash-based deduplication

3. **AI Summarizer** (`summarizer.py`)
   - Leverages OpenAI GPT-4o for intelligent article summarization
   - Tailors content specifically for meeting planner audience
   - Generates compelling subject lines and preview text

4. **Newsletter Builder** (`builder.py`)
   - Creates multiple output formats (HTML, Markdown, text)
   - Uses Jinja2 templating for consistent formatting
   - Optimized for email delivery platforms

5. **Sponsor Manager** (`sponsor_manager.py`)
   - Rotates sponsor content automatically
   - Tracks rotation history and state persistence
   - Supports multiple active sponsors with fair rotation

### Web Interface

6. **Flask Application** (`app.py`)
   - Provides dashboard for newsletter preview and management
   - Offers real-time statistics and system status
   - Includes manual newsletter generation capabilities

### Configuration and Templates

7. **Configuration System** (`config.json`)
   - Centralized settings for RSS sources, sponsors, and output preferences
   - Easily configurable without code changes
   - Supports sponsor rotation and email formatting settings

8. **Template System** (`templates/`)
   - Professional email-optimized HTML templates
   - Bootstrap-based web dashboard interface
   - Responsive design for multiple device types

## Data Flow

1. **Content Acquisition**: RSS feeds are scraped based on configured sources
2. **Deduplication**: New articles are checked against historical data to prevent duplicates
3. **Content Enhancement**: Articles are processed through OpenAI for summarization and formatting
4. **Sponsor Integration**: Current sponsor content is injected based on rotation schedule
5. **Newsletter Assembly**: All components are combined using Jinja2 templates
6. **Multi-format Output**: Final newsletters are generated in HTML, Markdown, and text formats
7. **Web Preview**: Flask interface provides preview and management capabilities

## External Dependencies

### APIs and Services
- **OpenAI GPT-4o**: For article summarization and subject line generation (requires API key)
- **RSS Feeds**: Multiple meeting industry sources for content aggregation

### Python Libraries
- **Flask**: Web framework for dashboard interface
- **feedparser**: RSS feed processing
- **trafilatura**: Content extraction and fallback parsing
- **Jinja2**: Template rendering for newsletters
- **OpenAI**: Python client for GPT-4o integration

### Data Storage
- **PostgreSQL Database**: Primary data persistence for articles, newsletters, sponsors, and analytics
- **JSON Files**: Legacy configuration and backup data storage
- **File System**: Newsletter output storage and template management

## Deployment Strategy

The application is designed for simple deployment with minimal infrastructure requirements:

### Current Architecture
- **Single-server deployment** suitable for Replit or similar platforms
- **PostgreSQL database** for robust data persistence and analytics
- **File-based configuration** for settings and templates
- **Environment variable configuration** for sensitive data (API keys, database credentials)
- **Static file serving** through Flask for CSS and assets

### Scalability Considerations
- PostgreSQL database provides robust data persistence and query capabilities
- Database-backed article deduplication and sponsor rotation
- Service-oriented architecture supports microservice decomposition
- Template system enables easy customization and branding
- API-based AI integration allows for provider switching if needed
- Analytics and reporting capabilities through database queries

### Security and Configuration
- Environment variables for sensitive configuration (API keys)
- Secret key configuration for Flask sessions
- Configurable logging levels and output destinations
- Error handling and graceful degradation for external service failures

The system prioritizes simplicity and reliability while maintaining professional output quality suitable for business newsletter distribution.

## Recent Changes (2025-07-17)

- **Database Integration**: Added PostgreSQL database with comprehensive data models for articles, newsletters, sponsors, and analytics
- **Enhanced Data Persistence**: Migrated from JSON-based storage to database-backed article tracking and sponsor management
- **Database Models**: Created models for Article, Newsletter, Sponsor, RSSSource, and supporting tables with proper relationships
- **Analytics Capabilities**: Added database-backed statistics and reporting for articles, newsletters, and sponsor performance
- **Migration Support**: Implemented automatic migration from existing JSON data to database structures
- **Web Dashboard Updates**: Updated Flask interface to use database statistics and management functions
- **Brand Update**: Implemented PlannerPulse brand style guide with official color palette (Primary: #636FEE, Secondary: #243C5A, Light: #E5E9F7, Gray: #5C6269) and Inter font family across all templates and CSS
- **Settings Page**: Completed full-featured settings page with RSS source management, sponsor activation/deactivation, and email configuration
- **RSS Feed Management**: Removed meetingsnet.com from RSS sources and added database methods for source management