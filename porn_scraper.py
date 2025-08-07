import tempfile
import shutil
import uuid
import tldextract
import requests
from collections import deque
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import shutil as sh

from keywords import PORN_KEYWORDS

# ===== CONFIG =====
START_URLS = [
    "https://qingse.one",
    "https://91porna.com/comic/index/av",
    "https://diaoda.co",
    "https://141jj.com/",
    "https://topavmap.com/",
    "https://tw.xchina.co/",
    "https://besides.xmgcxzy.org/",
    "https://9night.in/",
    "https://avday.app/",
]
OUTPUT_FILE = "blocklist.txt"
SAFE_DOMAINS = {"t.me", "telegram.org"}
MAX_LINKS = 1000
MAX_DEPTH = 0


# ===================
def get_browser_paths():
    chrome_bin = sh.which("chromium") or sh.which("google-chrome") or sh.which("chrome")
    driver_path = sh.which("chromedriver")
    if not chrome_bin or not driver_path:
        raise FileNotFoundError(
            f"Could not find browser or driver: chrome_bin={chrome_bin}, driver_path={driver_path}"
        )
    return chrome_bin, driver_path


def is_porn_link(text):
    return any(kw.lower() in text.lower() for kw in PORN_KEYWORDS)


def clean_domain(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower() if parsed.netloc else None
    if not host:
        return None
    # Remove port if present
    host = host.split(":")[0]
    # Skip punycode domains
    if host.startswith("xn--"):
        return None
    # Extract root domain using tldextract
    extracted = tldextract.extract(host)
    if extracted.domain and extracted.suffix:
        root_domain = f"{extracted.domain}.{extracted.suffix}"
        if root_domain not in SAFE_DOMAINS:
            return root_domain
    return None


def scrape_site(start_url):
    domains = set()
    visited = set()
    queue = deque([(start_url, 0)])

    chrome_bin, driver_path = get_browser_paths()

    while queue:
        url, depth = queue.popleft()
        print(f"[DEBUG] Queue size: {len(queue)}, Visiting: {url}, Depth: {depth}")
        if url in visited:
            print(f"[DEBUG] Skipping already visited: {url}")
            continue
        if depth > MAX_DEPTH:
            print(f"[DEBUG] Skipping due to depth limit: {url}")
            continue
        if len(visited) >= MAX_LINKS:
            print(f"[DEBUG] Reached MAX_LINKS limit: {MAX_LINKS}")
            break

        visited.add(url)

        temp_profile = tempfile.mkdtemp(prefix=f"selenium_{uuid.uuid4()}_")
        options = Options()
        options.binary_location = chrome_bin
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.page_load_strategy = "eager"

        service = Service(driver_path)
        driver = None
        try:
            print(f"[DEBUG] Launching browser for: {url}")
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(120)
            print(f"[DEBUG] Navigating to: {url}")
            driver.get(url)
            driver.execute_cdp_cmd("Network.enable", {})
            driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp", "*.css", "*.woff", "*.ttf", "*.otf", "*.svg", "*.mp4", "*.webm"]})
            print(f"[DEBUG] Page loaded for: {url}")
            driver.implicitly_wait(10)

            # Debug - capture a screenshot
            # if "avday.app" in url:
            #     try:
            #         driver.save_screenshot(f"avday_{uuid.uuid4()}.png")
            #         print(f"[DEBUG] Screenshot saved for {url}")
            #     except Exception as screenshot_err:
            #         print(f"[ERROR] Failed to capture screenshot: {screenshot_err}")

            elements = driver.find_elements("tag name", "a")
            print(f"[DEBUG] Found {len(elements)} links on: {url}")
            for a in elements:
                href = a.get_attribute("href") or ""
                text = a.text or ""

                if is_porn_link(href) or is_porn_link(text):
                    domain = clean_domain(href)
                    if domain and domain not in domains:
                        domains.add(domain)
                        print(f"[DEBUG] Added porn domain: {domain}")

                if href.startswith(start_url) and depth < MAX_DEPTH:
                    queue.append((href, depth + 1))
                    print(f"[DEBUG] Added to queue: {href}")

        except Exception as e:
            print(f"[ERROR] Could not scrape {url} - {e}")
        finally:
            if driver:
                driver.quit()
            shutil.rmtree(temp_profile, ignore_errors=True)

    return domains


def check_domain_and_content(domain):
    headers = {
        # More browser-like UA to bypass Cloudflare & entrance pages
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115 Safari/537.36"
    }
    for scheme in ["https://"]:
        for candidate in [domain, "www." + domain if not domain.startswith("www.") else None]:
            if not candidate:
                continue
            url = scheme + candidate
            try:
                r = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
                r.encoding = r.apparent_encoding
                html = r.text.lower()

                # Debug output for specific domain
                # if "https://topavmap.com/" in domain:
                #     print(f"[DEBUG] Raw HTML for {domain} [URL: {url}]")
                #     print(html)

                for kw in PORN_KEYWORDS:
                    if kw.lower() in html:
                        print(f"[DEBUG] Alive & porn: {domain} [keyword: {kw}] [URL: {url}]")
                        return True, True  # Alive & porn

                return True, False  # Alive but no porn keywords
            except requests.RequestException as e:
                print(f"[DEBUG] Dead: {domain} [URL: {url}]")
                continue
    return False, False


if __name__ == "__main__":
    from selenium.common.exceptions import TimeoutException

    all_domains = set()

    for site in START_URLS:
        print(f"[INFO] Starting scrape for {site}")
        try:
            found = scrape_site(site)
            print(f"[INFO] Completed scrape for {site}, found {len(found)} domains.")
        except TimeoutException:
            print(f"[WARN] Timeout while scraping {site}, skipping...")
            found = set()
        except Exception as e:
            print(f"[ERROR] Unexpected error while scraping {site}")
            found = set()
        all_domains.update(found)

    print(f"[INFO] Checking {len(all_domains)} domains for availability and porn content...")
    alive_porn_domains = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_domain = {executor.submit(check_domain_and_content, d): d for d in all_domains}
        for future in as_completed(future_to_domain):
            domain = future_to_domain[future]
            try:
                alive, porn = future.result()
                if alive and porn:
                    alive_porn_domains.append(domain)
                elif alive:
                    print(f"[DEBUG] Alive but no porn content: {domain}")
                else:
                    print(f"[DEBUG] Dead: {domain}")
            except Exception as e:
                print(f"[ERROR] Checking {domain} failed: {e}")

    # Load existing content from OUTPUT_FILE
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()
    except FileNotFoundError:
        existing_lines = []

    existing_domains = set()
    other_lines = []
    in_porn_section = False

    updated_lines = []
    added = False

    for line in existing_lines:
        line = line.rstrip()
        if line.strip().lower() == "# type: porn":
            in_porn_section = True
            other_lines.append(line)
            continue
        if in_porn_section and line.startswith("0.0.0.0"):
            parts = line.split()
            if len(parts) == 2:
                existing_domains.add(parts[1])
        else:
            other_lines.append(line)

    # Add new porn domains (deduplicated)
    new_domains = sorted(set(alive_porn_domains) - existing_domains)

    for line in other_lines:
        updated_lines.append(line)
        if line.strip().lower() == "# type: porn" and not added:
            for d in new_domains:
                updated_lines.append(f"0.0.0.0 {d}")
            added = True

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines) + "\n")

    print(f"[DONE] Saved {len(alive_porn_domains)} alive porn domains to {OUTPUT_FILE} in blocklist format")
