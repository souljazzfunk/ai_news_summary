# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains a collection of Python scripts for aggregating, summarizing, and sharing AI news from various sources. The system fetches content from RSS feeds, newsletters, and websites, processes them using Google's Gemini AI, and optionally posts summaries to social media platforms.

## Key Components

### Core Scripts
- **`rss_summary.py`** - Main RSS feed processor for Google Alerts, posts to X (Twitter)
- **`ai_news.py`** - Processes AI News newsletter from Buttondown archive
- **`smol_news_summary.py`** - Processes Smol AI newsletter content
- **`the_batch.py`** - Processes The Batch newsletter from DeepLearning.AI
- **`rundown.py`** - Processes The Rundown AI newsletter content
- **`KindleDeals.py`** - Handles Kindle deals (separate functionality)

### Support Files
- **`run_rss_summary.sh`** - Bash script for automated execution with cron jobs
- **`last_date.txt`** - Tracks last processed article dates to avoid duplicates
- **`rss_summary.cron.log`** - Log file for scheduled executions

## Environment Setup

### Dependencies
Install required packages manually via pip:
```bash
pip install feedparser requests beautifulsoup4 google-generativeai tweepy python-dotenv
```

### Virtual Environment
The system expects a virtual environment at `.venv/`:
```bash
python3 -m venv .venv
source .venv/bin/activate  # or .venv/bin/python for direct execution
```

### Environment Variables
Create a `.env` file with:
```
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_API_KEY=your_gemini_api_key  # fallback
X_CONSUMER_KEY=your_x_consumer_key
X_CONSUMER_SECRET=your_x_consumer_secret
X_ACCESS_TOKEN=your_x_access_token
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret
```

## Common Development Tasks

### Running Individual Scripts
```bash
# Run RSS summary with X posting
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

### Automated Execution
Use the provided shell script for cron jobs:
```bash
./run_rss_summary.sh
```

### Testing Without Social Media
Scripts automatically skip X posting if credentials are missing, useful for testing content generation.

## Architecture Notes

### Content Processing Flow
1. **Fetch** - Scripts retrieve content from RSS feeds, HTML pages, or APIs
2. **Extract** - BeautifulSoup parses HTML/XML to extract relevant text
3. **Normalize** - URLs are cleaned of tracking parameters and redirects resolved
4. **Summarize** - Gemini AI processes content into Japanese summaries
5. **Post** - Formatted content is shared via X API (optional)

### URL Normalization
The `rss_summary.py` script includes sophisticated URL processing:
- Extracts real URLs from Google redirects
- Follows redirect chains to final destinations  
- Strips tracking parameters (utm_*, fbclid, etc.)
- Handles both individual URLs and URLs within text content

### AI Processing
All scripts use Google's Gemini models (typically `gemini-2.5-flash-lite-preview-06-17`) with detailed Japanese prompts for:
- Content summarization
- Technical term explanation
- Translation from English to Japanese
- Formatting for social media constraints

### Error Handling
- Network timeouts and retries built into HTTP requests
- Graceful fallback when content extraction fails
- Comprehensive logging for cron job execution
- Missing credential detection with informational warnings

## Important Implementation Details

### Social Media Integration
- Uses Tweepy v2 Client for X API integration
- Automatic text truncation to fit 280-character limit
- URL length consideration in post formatting

### Content Sources
- **RSS Feeds**: Google Alerts, The Rundown AI
- **Newsletter Archives**: AI News (Buttondown), Smol AI, The Batch
- **Dynamic Content**: Fetches latest articles automatically

### Japanese Localization
All scripts include specific instructions for Japanese translation with technical terminology preferences (e.g., "オープンウェイトモデル" for open-weight models).

## Security Notes

### API Key Management
- API keys are stored in `.env` file (not tracked in git)
- Some scripts contain hardcoded API keys that should be moved to environment variables
- Scripts gracefully handle missing credentials

### Content Validation
- BeautifulSoup used for safe HTML parsing
- Request timeouts prevent hanging
- User-Agent headers set to avoid blocking
- KindleDeals.py is reference code for a working example of tweepy