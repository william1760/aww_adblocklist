# Block List for Ads and phishing and porn websites
# 🛡️ AWW Block List & Porn Scraper

This project provides a combined blocklist of Ads, Phishing, and Porn websites. It includes a static `blocklist.txt` for Pi-hole, AdGuard, or other DNS-based filtering systems and a Python scraper script to dynamically expand the list by scraping known pornographic sites.

---

## 📁 Files Overview

- `blocklist.txt`  
  A categorized domain block list:
  - `# Type: Ads`
  - `# Type: Phishing`
  - `# Type: Porn`

- `porn_scraper.py`  
  A Python script that:
  - Extracts porn links from configured source URLs
  - Checks if domains are active and contain porn content
  - Updates the blocklist under `# Type: Porn`

---

## ⚙️ How to Use

### Run Locally
```bash
python3 porn_scraper.py
```

### Run in Docker

1. Build the Docker image and start the container:
```bash
docker-compose up --build -d
```

2. Access the container shell:
```bash
docker exec -it porn_scraper bash
```

3. Run the scraper inside the container:
```bash
python3 porn_scraper.py
```

---

## 📌 Notes

- The scraper uses Playwright to render and analyze websites.
- It attempts to load root domains and `www.` versions for keyword checks.
- All results are automatically merged into the existing `blocklist.txt` file under the appropriate section.