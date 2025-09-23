"""
Twitter/X text validation utilities for proper character counting and text sanitization.

This module implements X's weighted character counting system to prevent tweets from
being collapsed with "Show more" links due to exceeding the 280 weighted character limit.
"""

import re
import unicodedata
from urllib.parse import urlparse


class TwitterTextValidator:
    """
    Validates and processes text for Twitter/X according to their weighted character system.

    X uses a weighted system where:
    - Most ASCII characters count as 1
    - CJK characters (Japanese, Chinese, Korean) count as 2
    - Emoji count as 2
    - URLs count as 23 characters each
    - Some invisible characters count as 1-2
    """

    # X's weighted character ranges (weight 1, all others default to weight 2)
    WEIGHT_1_RANGES = [
        (0x0000, 0x10FF),  # Latin-1, European scripts
        (0x2000, 0x200D),  # General punctuation, including ZWJ
        (0x2010, 0x201F),  # More punctuation
        (0x2032, 0x2037),  # Quotation marks
    ]

    # Invisible/problematic characters to remove
    INVISIBLE_CHARS = [
        '\u200B',  # Zero-Width Space (ZWSP)
        '\u200C',  # Zero-Width Non-Joiner (ZWNJ)
        '\u200E',  # Left-to-Right Mark (LRM)
        '\u200F',  # Right-to-Left Mark (RLM)
        '\u2060',  # Word Joiner
        '\uFEFF',  # Zero-Width No-Break Space (BOM)
        '\u2028',  # Line Separator
        '\u2029',  # Paragraph Separator
        '\u00AD',  # Soft Hyphen
    ]

    # URL pattern for counting
    URL_PATTERN = re.compile(r'https?://[^\s<>"]+')

    @classmethod
    def get_character_weight(cls, char):
        """Get the weighted character count for a single character."""
        code_point = ord(char)

        # Check if character falls in weight-1 ranges
        for start, end in cls.WEIGHT_1_RANGES:
            if start <= code_point <= end:
                return 1

        # Default weight is 2 for all other characters
        return 2

    @classmethod
    def calculate_weighted_length(cls, text):
        """
        Calculate the weighted character length as X counts it.

        Args:
            text (str): The text to analyze

        Returns:
            dict: Contains 'weighted_length', 'url_count', 'char_breakdown'
        """
        if not text:
            return {
                'weighted_length': 0,
                'url_count': 0,
                'char_breakdown': {'weight_1': 0, 'weight_2': 0, 'urls': 0}
            }

        # Find and replace URLs with placeholder for counting
        urls = cls.URL_PATTERN.findall(text)
        text_without_urls = cls.URL_PATTERN.sub('', text)

        # Count characters by weight
        weight_1_count = 0
        weight_2_count = 0

        for char in text_without_urls:
            if cls.get_character_weight(char) == 1:
                weight_1_count += 1
            else:
                weight_2_count += 1

        # URLs count as 23 characters each
        url_chars = len(urls) * 23

        # Total weighted length
        weighted_length = weight_1_count + (weight_2_count * 2) + url_chars

        return {
            'weighted_length': weighted_length,
            'url_count': len(urls),
            'char_breakdown': {
                'weight_1': weight_1_count,
                'weight_2': weight_2_count,
                'urls': url_chars
            }
        }

    @classmethod
    def remove_invisible_chars(cls, text):
        """Remove invisible and problematic Unicode characters."""
        if not text:
            return text

        # Remove specific invisible characters
        for char in cls.INVISIBLE_CHARS:
            text = text.replace(char, '')

        # Remove other control characters except common whitespace
        text = ''.join(char for char in text
                      if not (unicodedata.category(char).startswith('C')
                              and char not in '\n\r\t '))

        return text

    @classmethod
    def normalize_text(cls, text):
        """
        Normalize text to NFC form and remove problematic characters.

        Args:
            text (str): Input text

        Returns:
            str: Normalized and sanitized text
        """
        if not text:
            return text

        # Normalize to NFC (as X requires)
        text = unicodedata.normalize('NFC', text)

        # Remove invisible characters
        text = cls.remove_invisible_chars(text)

        # Clean up multiple whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @classmethod
    def validate_tweet_length(cls, text, max_length=280):
        """
        Validate if text fits within X's character limit.

        Args:
            text (str): Text to validate
            max_length (int): Maximum weighted character limit (default 280)

        Returns:
            dict: Validation result with details
        """
        normalized_text = cls.normalize_text(text)
        length_info = cls.calculate_weighted_length(normalized_text)

        is_valid = length_info['weighted_length'] <= max_length
        chars_over = max(0, length_info['weighted_length'] - max_length)

        return {
            'is_valid': is_valid,
            'normalized_text': normalized_text,
            'weighted_length': length_info['weighted_length'],
            'chars_over': chars_over,
            'max_length': max_length,
            'url_count': length_info['url_count'],
            'char_breakdown': length_info['char_breakdown']
        }

    @classmethod
    def truncate_to_limit(cls, text, max_length=280, ellipsis='…'):
        """
        Truncate text to fit within the weighted character limit.

        Special handling: If text ends with a URL, preserve the URL and truncate the text before it.

        Args:
            text (str): Text to truncate
            max_length (int): Maximum weighted character limit
            ellipsis (str): Ellipsis to add if truncated

        Returns:
            dict: Contains 'text', 'was_truncated', 'final_length'
        """
        normalized_text = cls.normalize_text(text)

        # Check if already within limit
        validation = cls.validate_tweet_length(normalized_text, max_length)
        if validation['is_valid']:
            return {
                'text': normalized_text,
                'was_truncated': False,
                'final_length': validation['weighted_length']
            }

        # Check if text ends with URL (patterns: "text\nURL" or "text URL")
        lines = normalized_text.split('\n')
        has_trailing_url = False
        trailing_url = ""
        main_text = normalized_text

        # Check for URL on separate line
        if len(lines) >= 2:
            potential_url = lines[-1].strip()
            if cls.URL_PATTERN.match(potential_url):
                has_trailing_url = True
                trailing_url = f"\n{potential_url}"
                main_text = '\n'.join(lines[:-1])
        else:
            # Check for URL at end of single line (space-separated)
            words = normalized_text.split()
            if len(words) >= 2:
                potential_url = words[-1]
                if cls.URL_PATTERN.match(potential_url):
                    has_trailing_url = True
                    trailing_url = f" {potential_url}"
                    main_text = ' '.join(words[:-1])

        if has_trailing_url:
            # Calculate space available for main text
            url_weight = cls.calculate_weighted_length(trailing_url)['weighted_length']
            ellipsis_weight = cls.calculate_weighted_length(ellipsis)['weighted_length']
            available_weight = max_length - url_weight - ellipsis_weight

            if available_weight <= 0:
                # Can't fit anything, return just the URL
                return {
                    'text': potential_url,
                    'was_truncated': True,
                    'final_length': cls.calculate_weighted_length(potential_url)['weighted_length']
                }

            # Binary search for optimal truncation point of main text
            left, right = 0, len(main_text)
            best_pos = 0

            while left <= right:
                mid = (left + right) // 2
                test_text = main_text[:mid]
                test_length = cls.calculate_weighted_length(test_text)['weighted_length']

                if test_length <= available_weight:
                    best_pos = mid
                    left = mid + 1
                else:
                    right = mid - 1

            # Truncate main text and add ellipsis + URL
            truncated_main = main_text[:best_pos].rstrip()
            if truncated_main:
                truncated_text = truncated_main + ellipsis + trailing_url
            else:
                truncated_text = trailing_url.strip()
        else:
            # No trailing URL, truncate normally
            ellipsis_weight = cls.calculate_weighted_length(ellipsis)['weighted_length']
            target_length = max_length - ellipsis_weight

            # Binary search for optimal truncation point
            left, right = 0, len(normalized_text)
            best_pos = 0

            while left <= right:
                mid = (left + right) // 2
                test_text = normalized_text[:mid]
                test_length = cls.calculate_weighted_length(test_text)['weighted_length']

                if test_length <= target_length:
                    best_pos = mid
                    left = mid + 1
                else:
                    right = mid - 1

            # Truncate and add ellipsis
            truncated_text = normalized_text[:best_pos].rstrip() + ellipsis

        final_length = cls.calculate_weighted_length(truncated_text)['weighted_length']

        return {
            'text': truncated_text,
            'was_truncated': True,
            'final_length': final_length
        }


def validate_post_text(text, max_length=280, debug=False):
    """
    Convenience function to validate post text.

    Args:
        text (str): Text to validate
        max_length (int): Maximum character limit
        debug (bool): Print debug information

    Returns:
        dict: Validation result
    """
    result = TwitterTextValidator.validate_tweet_length(text, max_length)

    if debug:
        print(f"Text: {text[:50]}{'...' if len(text) > 50 else ''}")
        print(f"Weighted length: {result['weighted_length']}/{max_length}")
        print(f"Valid: {result['is_valid']}")
        if not result['is_valid']:
            print(f"Over by: {result['chars_over']} weighted characters")
        print(f"Character breakdown: {result['char_breakdown']}")
        print(f"URLs found: {result['url_count']}")
        print("---")

    return result


def safe_truncate_post(text, max_length=280):
    """
    Safely truncate text to fit X's character limit.

    Args:
        text (str): Text to process
        max_length (int): Maximum character limit

    Returns:
        str: Truncated text that fits within limit
    """
    result = TwitterTextValidator.truncate_to_limit(text, max_length)
    return result['text']


# Quick validation functions for backward compatibility
def is_tweet_too_long(text, max_length=280):
    """Check if tweet exceeds weighted character limit."""
    return not TwitterTextValidator.validate_tweet_length(text, max_length)['is_valid']


def get_weighted_length(text):
    """Get the weighted character count for text."""
    return TwitterTextValidator.calculate_weighted_length(text)['weighted_length']