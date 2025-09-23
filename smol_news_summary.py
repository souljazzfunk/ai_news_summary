import requests
from bs4 import BeautifulSoup
import os
import time

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
from dotenv import load_dotenv
import google.generativeai as genai


def get_latest_issue_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the link to the first issue
        first_issue_link = soup.select_one("li[data-post-title] a.block")
        if not first_issue_link:
            print("Error: Could not find the link to the first issue.")
            return None, None, None, None

        first_issue_url = "https://news.smol.ai" + first_issue_link["href"]

        # Navigate to the first issue page
        response = requests.get(first_issue_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        try:
            issue_title_element = soup.find("h1")
            if issue_title_element:
                issue_title = issue_title_element.text.strip()
                issue_number = issue_title.split("#")[1].strip() if "#" in issue_title else "N/A"
            else:
                issue_number = "N/A"
                issue_title = "N/A"
        except Exception as e:
            print(f"Error extracting issue title and number: {e}")
            issue_number = "N/A"
            issue_title = "N/A"

        # Extract the content from the issue page
        content_element = soup.find("main")  # Try finding the main content tag first
        if not content_element:
            content_element = soup.find("article", class_="prose")  # Fallback to original selector

        if content_element:
            content = content_element.get_text(separator="\n")
        else:
            print("Error: Could not find the content body. Content set to 'N/A'.")
            content = "N/A"
            print(f"Content value when error occurred: {content}")  # Added logging

        return content, issue_number, issue_title, first_issue_url
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None, None, None, None


def summarize_in_japanese(text, api_key, model, issue_number, issue_title, first_issue_url):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model)

    try:
        prompt = f"""
Translate the following title into Japanese and provide a summary of the text in Japanese.
- Find and pick top-five most fascinating and impactful news topics, summarize them, and add source links
- Source links should be raw URLs. No need for formatting.
- Add additional creative points of view and key takeaways to each summary, but do it without saying "creative points of view and key takeaways"
- Use the markers [TITLE_JP] and [SUMMARY_JP] to separate the translated title and the summary.

Source: {first_issue_url}
Issue: #{issue_number}
Title: {issue_title}
Text: {text}

Format:
[TITLE_JP]
[SUMMARY_JP]
"""
        response = model.generate_content(prompt)
        response_text = response.text

        # Parse the response to extract title and summary
        title_jp = "N/A"
        summary_jp = "N/A"

        title_marker = "[TITLE_JP]"
        summary_marker = "[SUMMARY_JP]"

        title_start = response_text.find(title_marker)
        summary_start = response_text.find(summary_marker)

        if title_start != -1 and summary_start != -1:
            # Extract title between TITLE_JP and SUMMARY_JP
            title_jp = response_text[title_start + len(title_marker) : summary_start].strip()
            # Extract summary after SUMMARY_JP
            summary_jp = response_text[summary_start + len(summary_marker) :].strip()
        elif title_start != -1:
            # If only title marker is found, assume the rest is the title
            title_jp = response_text[title_start + len(title_marker) :].strip()
        elif summary_start != -1:
            # If only summary marker is found, assume the rest is the summary
            summary_jp = response_text[summary_start + len(summary_marker) :].strip()
        else:
            # If no markers are found, return the whole response as summary and N/A for title
            summary_jp = response_text.strip()

        return title_jp, summary_jp
    except Exception as e:
        print(f"Error during summarization or translation: {e}")
        return "Error", f"Error summarizing in Japanese: {e}"


def main():
    url = "https://news.smol.ai/issues"
    model = "gemini-2.5-flash-lite-preview-06-17"
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

    if api_key is None:
        print("Error: GOOGLE_API_KEY environment variable not set.")
        return

    start_time = time.time()

    result = get_latest_issue_html(url)
    if result is None:
        print("Failed to retrieve HTML content.")
    else:
        html_content, issue_number, issue_title, first_issue_url = result
        japanese_title, japanese_summary = summarize_in_japanese(
            html_content, api_key, model, issue_number, issue_title, first_issue_url
        )
        print("AI News 解説 by " + model)
        print("出典：" + first_issue_url)
        print()
        print(f"Title: {japanese_title}")  # Print Japanese title
        print(f"Summary: {japanese_summary}")  # Added logging

    end_time = time.time()
    print(f"\n({end_time - start_time:.2f} seconds)")


if __name__ == "__main__":
    main()
