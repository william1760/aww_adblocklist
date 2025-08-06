import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

# Target site
START_URL = "https://91porna.com"

# Keywords for porn detection (Chinese + English)
PORN_KEYWORDS = [
    "成人", "无码", "黄色", "porn", "sex", "jav", "av", "性爱", "情色"
]

# Output file
OUTPUT_FILE = "porn_domains.txt"

def is_porn_link(text):
    """Check if text contains any porn keyword."""
    return any(keyword.lower() in text.lower() for keyword in PORN_KEYWORDS)

def get_links_from_page(url):
    """Fetch all links from a page."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        links = [a.get("href") for a in soup.find_all("a", href=True)]
        return links
    except Exception as e:
        print(f"[ERROR] Could not fetch {url} - {e}")
        return []

def clean_domain(url):
    """Extract clean domain from URL."""
    parsed = urlparse(url)
    return parsed.netloc.lower() if parsed.netloc else None

def main():
    print(f"[INFO] Crawling {START_URL} for porn links...")
    all_links = get_links_from_page(START_URL)
    porn_domains = set()

    for link in all_links:
        if is_porn_link(link):
            domain = clean_domain(link)
            if domain and not domain.startswith("#"):
                porn_domains.add(domain)

    # Save to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for domain in sorted(porn_domains):
            f.write(domain + "\n")

    print(f"[DONE] Found {len(porn_domains)} porn domains. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()