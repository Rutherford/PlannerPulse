# PlannerPulse 📧

## AI-Powered Newsletter Generator for Meeting Planners

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1+-green.svg)](https://flask.palletsprojects.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-orange.svg)](https://openai.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791.svg)](https://postgresql.org)

PlannerPulse is an intelligent newsletter automation system that scrapes meeting industry sources, uses GPT-4o to summarize articles, and generates professional newsletters in multiple formats. Perfect for meeting planners, event professionals, and tourism boards who need to stay current with industry trends.

## ✨ Features

### 🤖 **AI-Powered Content Generation**

- **GPT-4o Integration**: Automatically summarizes articles with key takeaways
- **Smart Subject Lines**: Generates compelling email subject lines
- **Content Optimization**: Tailored specifically for meeting industry professionals

### 📰 **Multi-Source Content Aggregation**

- **RSS Feed Scraping**: Monitors 6+ leading industry publications
- **Duplicate Detection**: Smart deduplication using content hashing
- **Source Management**: Easy addition/removal of RSS sources via web interface

### 🎨 **Multi-Format Output**

- **HTML Newsletter**: Email-ready HTML with responsive design
- **Markdown Format**: GitHub/documentation-friendly format
- **Plain Text**: Email client compatibility
- **Beehiiv Ready**: Optimized for popular email platforms

### 💼 **Sponsor Management**

- **Automated Rotation**: Intelligent sponsor rotation system
- **CVB Integration**: Built-in support for Convention & Visitors Bureaus
- **Custom Messages**: Personalized sponsor content and links
- **Analytics Ready**: Track sponsor performance and usage

### 🗄️ **Database-Driven**

- **PostgreSQL Backend**: Reliable data storage and retrieval
- **Article History**: Complete archive of processed articles
- **Newsletter Archive**: Full history of generated newsletters
- **Analytics**: Built-in statistics and performance tracking

### 🌐 **Web Interface**

- **Live Dashboard**: Real-time statistics and monitoring
- **Preview System**: Review newsletters before sending
- **Configuration Management**: Update settings without code changes
- **Manual Controls**: Generate newsletters on-demand

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- OpenAI API key
- Git

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Rutherford/PlannerPulse.git
   cd PlannerPulse
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   # or with uv
   uv sync
   ```

3. **Set up environment variables**

   ```bash
   # Create .env file
   OPENAI_API_KEY=<your_openai_api_key>
   DATABASE_URL=postgresql://username:password@localhost/planner_pulse
   SECRET_KEY=<your_flask_secret_key>
   ```

4. **Initialize the database**

   ```bash
   python models.py
   ```

5. **Run the application**

   ```bash
   # Web interface
   python app.py

   # Command line generation
   python main.py
   ```

6. **Access the dashboard**

   Open <http://localhost:5000> in your browser

## 🏗️ Project Structure

```text
PlannerPulse/
├── app.py                 # Flask web application
├── main.py               # CLI newsletter generation
├── scraper.py            # RSS feed scraping
├── summarizer.py         # GPT-4o integration
├── builder.py            # Newsletter formatting
├── database.py           # Database managers
├── models.py             # SQLAlchemy models
├── deduplicator.py       # Article deduplication
├── sponsor_manager.py    # Sponsor rotation logic
├── config.json           # Configuration settings
├── pyproject.toml        # Project dependencies
├── templates/            # Jinja2 HTML templates
│   ├── base_template.html
│   └── preview.html
├── static/               # CSS and assets
│   └── style.css
├── output/               # Generated newsletters
│   ├── newsletter.html
│   ├── newsletter.md
│   └── newsletter.txt
└── data/                 # Data storage
    ├── article_history_backup.json
    └── sponsor_state.json
```

## 📊 Database Schema

### Core Tables

- **Articles**: Store all scraped articles with metadata
- **Newsletters**: Archive of generated newsletters
- **Sponsors**: Manage sponsor information and rotation
- **RSS Sources**: Configure and monitor feed sources
- **Newsletter Articles**: Many-to-many relationship tracking

### Key Features

- Automatic timestamp tracking
- JSON fields for flexible data storage
- Foreign key relationships for data integrity
- Built-in analytics and statistics

## 🔧 Configuration

Edit `config.json` to customize:

```json
{
  "newsletter_title": "Planner Pulse",
  "sources": [
    "https://www.meetingstoday.com/rss.xml",
    "https://www.bizbash.com/rss.xml",
    "https://www.tsnn.com/news/rss.xml"
  ],
  "sponsors": [
    {
      "name": "Visit St. Pete Clearwater",
      "message": "Your sponsor message here...",
      "link": "https://www.visitstpeteclearwater.com/meetings",
      "active": true
    }
  ],
  "content_settings": {
    "articles_per_newsletter": 8,
    "summary_max_length": 200
  }
}
```

## 🎯 Target Audience

**Perfect for:**

- 📅 Meeting planners and event professionals
- 🏨 Convention & Visitors Bureaus (CVBs)
- 🏢 Corporate event teams
- 📰 Industry publications and blogs
- 🎪 Event marketing agencies

## 🔌 API Endpoints

### Dashboard

- `GET /` - Main dashboard with statistics
- `GET /preview` - Preview latest newsletter
- `POST /generate` - Generate new newsletter

### Settings Management

- `POST /api/settings/rss` - Add RSS source
- `DELETE /api/settings/rss` - Remove RSS source
- `POST /api/settings/sponsor` - Add sponsor
- `POST /api/rotate-sponsor` - Manual sponsor rotation

### Statistics

- `GET /api/stats` - Get dashboard statistics

## 🧪 Usage Examples

### Generate Newsletter (CLI)

```bash
python main.py
# Output: ✅ Newsletter generated successfully! Check /output/ directory
```

### Web Interface

1. Visit <http://localhost:5000>
2. View current statistics and recent newsletters
3. Click "Generate Newsletter" to create new edition
4. Preview generated content before distribution

### Integration with Email Platforms

The generated HTML is optimized for:

- 📧 Beehiiv
- 📬 MailerLite  
- 📮 Mailchimp
- 📨 ConvertKit
- 📧 Any HTML email editor

## 🛠️ Technical Details

### Dependencies

- **Flask**: Web framework and UI
- **SQLAlchemy**: Database ORM
- **OpenAI**: GPT-4o API integration
- **Feedparser**: RSS feed parsing
- **BeautifulSoup4**: HTML parsing
- **Trafilatura**: Full-text article extraction
- **Jinja2**: Template engine
- **PostgreSQL**: Database backend

### AI Integration

- Uses OpenAI's GPT-4o model for summarization
- Custom prompts optimized for meeting industry content
- Automatic key takeaway extraction
- Subject line generation with length optimization

### Performance Features

- Database connection pooling
- Efficient duplicate detection using MD5 hashing
- Async-ready architecture
- Error handling and logging

## 📈 Analytics & Monitoring

Track performance with built-in analytics:

- Articles processed per day
- Newsletter generation statistics
- Source performance metrics
- Sponsor rotation tracking
- Error monitoring and logging

## 🔮 Future Enhancements

- [ ] **Email Integration**: Direct sending via SMTP/API
- [ ] **Social Media**: Auto-posting to LinkedIn/Twitter
- [ ] **Mobile App**: React Native companion app
- [ ] **Analytics Dashboard**: Advanced reporting and insights
- [ ] **Multi-Language**: Support for international audiences
- [ ] **White Label**: Customizable branding options

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📧 Email: <support@plannerpulse.com>
- 💬 GitHub Issues: [Report a bug](https://github.com/Rutherford/PlannerPulse/issues)
- 📖 Documentation: [Wiki](https://github.com/Rutherford/PlannerPulse/wiki)

## 🙏 Acknowledgments

- Meeting industry publications for RSS feed access
- OpenAI for GPT-4o API
- The Flask and SQLAlchemy communities
- Convention & Visitors Bureaus for content inspiration

---

## Made with ❤️ for the meeting and events industry

*PlannerPulse - Keeping meeting planners informed, one pulse at a time.*
