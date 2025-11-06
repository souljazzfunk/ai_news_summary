# AI News Summary

A collection of Python scripts for aggregating, summarizing, and sharing AI news from various sources. The system fetches content from RSS feeds, newsletters, and websites, processes them using Google's Gemini AI, and optionally posts summaries to social media platforms.

## Features

- **RSS Feed Processing**: Aggregates AI news from Google Alerts and other RSS sources
- **Newsletter Processing**: Extracts and summarizes content from popular AI newsletters
- **AI-Powered Summarization**: Uses Google's Gemini AI to generate Japanese summaries
- **Social Media Integration**: Optional posting to X (Twitter)
- **Automated Execution**: Cron job support for scheduled processing

## Supported Sources

- **Google Alerts RSS** - General AI news aggregation
- **AI News** - Newsletter from Buttondown
- **Smol AI** - AI newsletter content
- **The Batch** - DeepLearning.AI newsletter
- **The Rundown AI** - Daily AI newsletter

## Requirements

- Python 3.7+
- Google Gemini API key
- X (Twitter) API credentials (optional, for posting)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai_news_summary
```

2. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install feedparser requests beautifulsoup4 google-generativeai tweepy python-dotenv
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Configuration

Create a `.env` file with the following variables:

```bash
# Google Gemini API Key (required)
GOOGLE_API_KEY=your_google_gemini_api_key_here
GEMINI_API_KEY=your_google_gemini_api_key_here

# X (Twitter) API Credentials (optional)
X_CONSUMER_KEY=your_x_consumer_key_here
X_CONSUMER_SECRET=your_x_consumer_secret_here
X_ACCESS_TOKEN=your_x_access_token_here
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret_here
```

### Getting API Keys

- **Google Gemini API**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **X API**: Create an app at [Twitter Developer Portal](https://developer.twitter.com/)

## Usage

Run individual scripts:

```bash
# Process RSS feeds from Google Alerts
python rss_summary.py

# Process AI News newsletter
python ai_news.py

# Process Smol AI newsletter
python smol_news_summary.py

# Process The Batch newsletter
python the_batch.py

# Process The Rundown AI newsletter
python rundown.py
```

### Testing Without Social Media

Scripts automatically skip X posting if credentials are missing. This is useful for testing content generation without publishing.

## Architecture

### Content Processing Flow

1. **Fetch** - Retrieve content from RSS feeds, HTML pages, or APIs
2. **Extract** - Parse HTML/XML to extract relevant text
3. **Normalize** - Clean URLs of tracking parameters and resolve redirects
4. **Summarize** - Process content with Gemini AI into Japanese summaries
5. **Post** - Share formatted content via X API (optional)

### URL Normalization

The RSS summary script includes sophisticated URL processing:
- Extracts real URLs from Google redirects
- Follows redirect chains to final destinations
- Strips tracking parameters (utm_*, fbclid, etc.)
- Handles URLs within text content

### AI Processing

All scripts use Google's Gemini models (typically `gemini-2.5-flash-lite-preview-06-17`) with detailed Japanese prompts for:
- Content summarization
- Technical term explanation
- Translation from English to Japanese
- Formatting for social media constraints

## Project Structure

```
ai_news_summary/
├── rss_summary.py          # Main RSS feed processor
├── ai_news.py              # AI News newsletter processor
├── smol_news_summary.py    # Smol AI newsletter processor
├── the_batch.py            # The Batch newsletter processor
├── rundown.py              # The Rundown AI processor
├── KindleDeals.py          # Kindle deals (separate functionality)
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
└── last_date.txt           # Tracks last processed dates
```

## Automation

For automated execution with cron jobs, create shell scripts similar to:

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/path/to/ai_news_summary"
PYBIN="$PROJECT_DIR/.venv/bin/python"

cd "$PROJECT_DIR"
"$PYBIN" "$PROJECT_DIR/rss_summary.py"
```

## Error Handling

The scripts include:
- Network timeouts and retries for HTTP requests
- Graceful fallback when content extraction fails
- Comprehensive logging for cron job execution
- Missing credential detection with informational warnings

## Security Notes

- API keys are stored in `.env` file (not tracked in git)
- Scripts gracefully handle missing credentials
- BeautifulSoup used for safe HTML parsing
- Request timeouts prevent hanging

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
