import requests
from bs4 import BeautifulSoup


def analyze_html(url):
    try:
        # Fetch the issues listing page
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the link to the first issue
        first_issue_link = soup.select_one("li[data-post-title] a.block")
        if not first_issue_link:
            print("Error: Could not find the link to the first issue on the listing page.")
            return

        first_issue_url = "https://news.smol.ai" + first_issue_link["href"]

        # Navigate to the first issue page
        response = requests.get(first_issue_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Print the structure of the HTML of the issue page
        print(soup.prettify())

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")


def main():
    url = "https://news.smol.ai/issues"
    analyze_html(url)


if __name__ == "__main__":
    main()
