# Rujhaan (Google Trends Fetcher)

This project fetches all trending terms from Google Trends (India) using Playwright.

## Prerequisites

- Python 3.7+
- pip

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:
   ```bash
   playwright install
   ```

## Usage

Run the script with the default region (India):
```bash
python main.py
```

Run for a specific region (e.g., United States):
```bash
python main.py --geo US 
```

Run with news articles (slower):
```bash
python main.py --news
```

or 

```bash
python main.py --geo US --news
```

The results will be saved to `trending_terms_{GEO}.json`.

## Project Explanation

### How it works
This project uses **Playwright**, a powerful browser automation tool, to scrape data from Google Trends.
1.  **Browser Automation**: It launches a headless Chromium browser (invisible to the user).
2.  **Navigation**: It goes to the Google Trends page for the specified region (e.g., `?geo=US`).
3.  **Data Extraction**: It iterates through the table rows, extracting the trending term, search volume, start time, and related queries.
4.  **Pagination**: It automatically clicks the "Next" button to load subsequent pages until all data is retrieved.

### Tools Used
-   **Python**: The programming language.
-   **Playwright**: For controlling the browser and scraping dynamic content.

### Cost
-   **Free**: This project uses open-source libraries and accesses a public website. There are no API costs or subscription fees involved.

## Production Readiness & Requirements

### Is it Production Ready?
This script is **MVP (Minimum Viable Product) ready** but requires additional work for a robust production service:
-   **Stability**: Web scrapers are inherently fragile. If Google changes their HTML structure (class names, layout), this script will break and require updates.
-   **Blocking**: Google aggressively blocks automated traffic. Running this frequently from a data center IP (like AWS/GCP) will likely result in CAPTCHAs or IP bans.
-   **Error Handling**: Production code needs robust retries, logging, and alerting.
-   **Deployment**: To deploy as a service, you would wrap this in an API (e.g., FastAPI) and run it in a container (Docker).

### Memory Requirements
-   **RAM**: Playwright launches a full Chromium browser instance. Expect **500MB - 1GB of RAM** per concurrent session.
-   **CPU**: Browser automation is CPU-intensive during page loads and rendering.
-   **Storage**: Minimal storage is needed for the script and JSON output.


