#!/usr/bin/env python3
"""
Test script to validate Twitter/X post character counting and detect issues.

This script tests the twitter_text_utils module with various edge cases
that commonly cause "Show more" problems on X.
"""

import sys
from twitter_text_utils import (
    TwitterTextValidator,
    validate_post_text,
    safe_truncate_post,
    get_weighted_length,
    is_tweet_too_long
)


def test_basic_ascii():
    """Test basic ASCII text."""
    print("=== Testing Basic ASCII ===")

    test_cases = [
        "Hello world!",  # 12 chars
        "A" * 280,       # Exactly 280 chars
        "A" * 281,       # Over limit
    ]

    for text in test_cases:
        result = validate_post_text(text, debug=True)
        print()


def test_japanese_text():
    """Test Japanese text (CJK characters count as 2)."""
    print("=== Testing Japanese Text ===")

    test_cases = [
        "こんにちは世界！",  # 8 Japanese chars = 16 weighted
        "あ" * 140,        # 140 Japanese chars = 280 weighted (exactly at limit)
        "あ" * 141,        # 141 Japanese chars = 282 weighted (over limit)
        "AIニュース要約です。今日の最新技術情報をお届けします。",  # Mixed content
        "AI News 今日のニュース",  # Mixed ASCII and Japanese
    ]

    for text in test_cases:
        result = validate_post_text(text, debug=True)
        print()


def test_urls_and_mixed_content():
    """Test URLs (count as 23 chars each) with mixed content."""
    print("=== Testing URLs and Mixed Content ===")

    test_cases = [
        "Check this out: https://example.com",
        "AI記事: https://example.com/very/long/path/that/would/normally/be/much/longer",
        "複数URL: https://site1.com https://site2.com",
        "日本語記事です。詳細はこちら: https://example.com/article/12345",
        "短いテキスト\nhttps://example.com",  # With newline
    ]

    for text in test_cases:
        result = validate_post_text(text, debug=True)
        print()


def test_invisible_characters():
    """Test invisible and problematic characters."""
    print("=== Testing Invisible Characters ===")

    # Create text with invisible characters
    base_text = "AIニュース"

    test_cases = [
        base_text + "\u200B" + "更新",        # Zero-Width Space
        base_text + "\u200C" + "情報",        # Zero-Width Non-Joiner
        base_text + "\u200E" + "テスト",       # Left-to-Right Mark
        base_text + "\u200F" + "右から左",     # Right-to-Left Mark
        base_text + "\u2060" + "単語結合",     # Word Joiner
        base_text + "\uFEFF" + "BOM文字",     # Zero-Width No-Break Space
        base_text + "\u00AD" + "ソフト",       # Soft Hyphen
        "Normal text\u200B\u200C\u200E\u200F\u2060\uFEFF with multiple invisible chars",
    ]

    for text in test_cases:
        print(f"Original text (len={len(text)}): {repr(text)}")
        result = validate_post_text(text, debug=True)
        print()


def test_emoji():
    """Test emoji (each counts as 2 weighted characters)."""
    print("=== Testing Emoji ===")

    test_cases = [
        "Hello 👋 World 🌍",
        "🤖 AI News 📰",
        "日本語ニュース 🇯🇵 です",
        "👨‍💻👩‍💻🤖",  # Complex emoji with ZWJ sequences
        "🎯" * 140,  # 140 emoji = 280 weighted (at limit)
        "🎯" * 141,  # 141 emoji = 282 weighted (over limit)
    ]

    for text in test_cases:
        result = validate_post_text(text, debug=True)
        print()


def test_realistic_posts():
    """Test realistic post scenarios similar to your AI news posts."""
    print("=== Testing Realistic AI News Posts ===")

    test_cases = [
        # Simulating rss_summary.py output
        "DeepSeekの新しいR1モデルが発表されました。オープンウェイトモデルとして高い性能を示しています。詳細はこちら。\nhttps://example.com/deepseek-r1",

        # Long Japanese summary that might get truncated
        "本日のAIニュースをお届けします。GoogleのGemini 2.0がリリースされ、従来モデルを大幅に上回る性能を実現。特に日本語処理能力が向上し、より自然な対話が可能になりました。また、Anthropicからも新しいClaude 4モデルが発表され、競争が激化しています。\nhttps://example.com/ai-news",

        # Mixed content with multiple URLs
        "AI業界アップデート: OpenAI https://openai.com, Anthropic https://anthropic.com, Google https://google.com の最新動向",

        # Edge case: mostly URL
        "記事: https://very-long-domain-name.com/extremely/long/path/to/article/with/many/segments/that/would/normally/exceed/limits",
    ]

    for text in test_cases:
        print(f"Testing realistic post:")
        result = validate_post_text(text, debug=True)

        if not result['is_valid']:
            print("POST TOO LONG - Testing truncation:")
            truncated_result = safe_truncate_post(text)
            print(f"Truncated: {truncated_result}")
            validate_post_text(truncated_result, debug=True)

        print("-" * 50)


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("=== Testing Edge Cases ===")

    test_cases = [
        "",  # Empty string
        " ",  # Single space
        "\n",  # Single newline
        "A",  # Single ASCII character
        "あ",  # Single Japanese character
        "🎯",  # Single emoji
        "https://x.com",  # Just a URL
        "\u200B" * 10,  # Only invisible characters
        "A" * 279 + "あ",  # 279 ASCII + 1 Japanese = 281 weighted (over by 1)
    ]

    for text in test_cases:
        print(f"Testing edge case: {repr(text)}")
        result = validate_post_text(text, debug=True)
        print()


def run_comprehensive_test():
    """Run all test suites."""
    print("Twitter/X Character Validation Test Suite")
    print("=" * 50)

    test_basic_ascii()
    test_japanese_text()
    test_urls_and_mixed_content()
    test_invisible_characters()
    test_emoji()
    test_realistic_posts()
    test_edge_cases()

    print("\n" + "=" * 50)
    print("Test completed! Check the debug output above for any issues.")
    print("Posts marked as 'Valid: False' would trigger 'Show more' on X.")


if __name__ == "__main__":
    run_comprehensive_test()