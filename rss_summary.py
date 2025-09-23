import feedparser
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import tweepy
import os
import re
import time
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, unquote
from twitter_text_utils import TwitterTextValidator, safe_truncate_post, validate_post_text

# .env を読み込む
load_dotenv()

# 環境変数からAPIキー等を取得（GOOGLE_API_KEY優先、なければGEMINI_API_KEY）
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
X_CONSUMER_KEY = os.getenv("X_CONSUMER_KEY")
X_CONSUMER_SECRET = os.getenv("X_CONSUMER_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")

RSS_URL = "https://www.google.com/alerts/feeds/11024000892133675470/5296472670452469910"

def _missing_x_creds():
    missing = []
    if not X_CONSUMER_KEY:
        missing.append("X_CONSUMER_KEY")
    if not X_CONSUMER_SECRET:
        missing.append("X_CONSUMER_SECRET")
    if not X_ACCESS_TOKEN:
        missing.append("X_ACCESS_TOKEN")
    if not X_ACCESS_TOKEN_SECRET:
        missing.append("X_ACCESS_TOKEN_SECRET")
    return missing

def fetch_latest_entries(rss_url, max_entries=3):
    feed = feedparser.parse(rss_url)
    return feed.entries[:max_entries]

def fetch_article_text(url):
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            )
        }
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        # より汎用的な本文抽出セレクタ
        paragraphs = soup.select("article p, main p, div[id*='content'] p, div[class*='content'] p, p")
        text = "\n".join([p.get_text(strip=True) for p in paragraphs])
        return text[:4000]
    except Exception:
        return ""


def _extract_from_google_redirect(url: str) -> str:
    parsed = urlparse(url)
    # google.com/url?url=... or ?q=...
    if parsed.netloc.endswith("google.com") and parsed.path == "/url":
        qs = parse_qs(parsed.query)
        dest = qs.get("url") or qs.get("q")
        if dest and len(dest) > 0:
            return unquote(dest[0])
    # images redirect
    if parsed.netloc.endswith("google.com") and parsed.path == "/imgres":
        qs = parse_qs(parsed.query)
        dest = qs.get("imgurl") or qs.get("url")
        if dest and len(dest) > 0:
            return unquote(dest[0])
    # news.google.com articles often embed url param
    if parsed.netloc.startswith("news.google."):
        qs = parse_qs(parsed.query)
        dest = qs.get("url") or qs.get("q")
        if dest and len(dest) > 0:
            return unquote(dest[0])
    return url


def _follow_redirects(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/126 Safari/537.36"}
        with requests.Session() as session:
            # Try HEAD first
            resp = session.head(url, headers=headers, allow_redirects=True, timeout=15)
            final_url = resp.url
            # Fallback to GET if HEAD not helpful
            if not final_url or resp.status_code >= 400:
                resp = session.get(url, headers=headers, allow_redirects=True, timeout=15, stream=True)
                final_url = resp.url
            return final_url or url
    except Exception:
        return url


def _strip_tracking_params(url: str) -> str:
    try:
        parsed = urlparse(url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        tracking_keys = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "utm_id",
            "gclid", "fbclid", "gbraid", "wbraid", "yclid", "mc_cid", "mc_eid", "igshid",
            "ved", "ei", "oq", "gs_lcr_"
        }
        filtered = {k: v for k, v in query.items() if k not in tracking_keys}
        new_query = urlencode(filtered, doseq=True)
        cleaned = parsed._replace(query=new_query, fragment="")
        return urlunparse(cleaned)
    except Exception:
        return url


def normalize_url(url: str) -> str:
    step1 = _extract_from_google_redirect(url)
    step2 = _follow_redirects(step1)
    step3 = _strip_tracking_params(step2)
    return step3


def normalize_text_urls(text: str, max_urls: int = 10) -> str:
    if not text:
        return text
    # Rough URL pattern; stop at whitespace or closing parens
    url_pattern = re.compile(r"https?://[^\s)<>]+")
    seen = set()
    replacements = {}
    for match in url_pattern.finditer(text):
        if len(replacements) >= max_urls:
            break
        raw = match.group(0)
        if raw in seen:
            continue
        seen.add(raw)
        normalized = normalize_url(raw)
        # Only replace if changed
        if normalized and normalized != raw:
            replacements[raw] = normalized
    if not replacements:
        return text
    # Replace longest first to avoid partial overlaps
    for raw in sorted(replacements.keys(), key=len, reverse=True):
        text = text.replace(raw, replacements[raw])
    return text


def strip_html_tags_from_text(raw_text: str) -> str:
    """
    Remove HTML tags from a given text string using BeautifulSoup.
    Falls back to a regex-based strip if parsing fails for any reason.
    """
    if not raw_text:
        return raw_text
    try:
        # Use html.parser to strip tags reliably
        return BeautifulSoup(raw_text, "html.parser").get_text(strip=False)
    except Exception:
        # Fallback: naive tag removal
        return re.sub(r"<[^>]+>", "", raw_text)

def summarize_with_gemini(text):
    if not API_KEY:
        print("Gemini API error: GOOGLE_API_KEY (or GEMINI_API_KEY) not set in environment/.env")
        return ""
    genai.configure(api_key=API_KEY, transport="rest")
    try:
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite-preview-06-17")
        prompt = f"""
以下の文章を要約してください。
- 出力は必ず日本語のみ。英語は使わないでください。
- です・ます調で簡潔に。
- 箇条書きで最大3行。
- 固有名詞・数値・URLは原文を尊重。

【文章】
{text}
"""
        response = model.generate_content(contents=prompt)
        return (response.text or "").strip()
    except Exception as e:
        print(f"Gemini API error: {e}")
        return ""

def post_to_x(text):
    # Align Tweepy auth with KindleDeals.py: use v2 Client with user context
    client = tweepy.Client(
        consumer_key=X_CONSUMER_KEY,
        consumer_secret=X_CONSUMER_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_TOKEN_SECRET,
    )
    client.create_tweet(text=text)

def main():
    missing = _missing_x_creds()
    if missing:
        print(f"[Posting] Warning: Missing X credentials: {', '.join(missing)}")
        print("[Posting] Will skip posting and only print the composed posts.")
    entries = fetch_latest_entries(RSS_URL)
    print(f"Feed: {len(entries)} entries found")
    # print(f"entries: {entries}")
    for entry in entries:
        raw_url = entry.link
        title = strip_html_tags_from_text(getattr(entry, "title", ""))
        final_url = normalize_url(raw_url)
        print(f"Fetching: {title[:60]}...")
        article_text = fetch_article_text(final_url)
        # フォールバック: RSSのsummary/descriptionを使用
        fallback_text = getattr(entry, "summary", "") or getattr(entry, "description", "")
        # 取得したテキスト内のURLも正規化（Google転送リンクを置換）
        source_text = article_text or fallback_text
        source_text = normalize_text_urls(source_text)
        if not source_text:
            continue
        print(f"Summarizing...")
        summary = summarize_with_gemini(source_text)
        # 生成されたサマリ内にURLが残る場合も正規化
        summary = normalize_text_urls(summary, max_urls=5)
        post_text = f"{summary}\n{final_url}"

        # Use proper weighted character validation
        validation = validate_post_text(post_text, debug=True)
        if not validation['is_valid']:
            # Calculate available space for summary (280 - URL length - newline)
            url_weight = TwitterTextValidator.calculate_weighted_length(f"\n{final_url}")['weighted_length']
            available_weight = 280 - url_weight

            if available_weight > 6:  # Reserve space for ellipsis
                truncated_summary = safe_truncate_post(summary, available_weight)
                post_text = f"{truncated_summary}\n{final_url}"
            else:
                post_text = final_url

        # Final validation with debug output
        final_validation = validate_post_text(post_text, debug=True)
        print(f"Posting: {post_text}\n")
        if not missing:
            try:
                post_to_x(post_text)
            except Exception as e:
                print(f"[Posting] Error posting to X: {e}\n")
        time.sleep(1)

if __name__ == "__main__":
    main()
