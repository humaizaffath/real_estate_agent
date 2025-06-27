# Berkeley and Charleston County Real Estate Document Scraper

## Overview

This project is an automation tool designed to scrape real estate documents from the public property websites of **Berkeley County** and **Charleston County**, South Carolina. It leverages the power of **Python** and **Playwright** for browser automation, combined with residential proxies from **Zyte Smart Proxy Manager** to bypass common anti-bot measures like Cloudflare and CAPTCHAs.

The scraper collects key documents such as **property cards**, **tax bills**, **receipts**, and **deed PDFs**, organizing them neatly by county and parcel numbers (TMS). The goal is to provide a reliable and repeatable solution for gathering these publicly available records efficiently.

---

## How It Works

- **Proxy Integration:** The scraper uses Zyte’s residential proxy service to mask requests and evade bot detection by websites.
- **Browser Automation:** Playwright is used to programmatically control Chromium browsers in a way that mimics human user behavior, including mouse movements, typing delays, and realistic navigation flows.
- **Human-like Interaction:** Random delays and mouse movements help reduce detection risk.
- **Page Navigation & Interaction:** The script automatically fills search forms, clicks necessary links/buttons, waits for content to load, and handles multi-step navigation sequences.
- **PDF Downloading:** After navigating to the relevant pages, the scraper generates PDFs of property cards, tax info, and deed documents.
- **CAPTCHA Handling:** When automated CAPTCHA solving is not implemented, the scraper pauses and prompts the user to manually solve CAPTCHAs.
- **Error Handling & Debugging:** Screenshots and HTML snapshots are saved when errors or unexpected page states occur to aid debugging.

---

## Steps Automated

1. **Property Card Retrieval:**
   - Input TMS number.
   - Navigate to the property card page.
   - Save a PDF of the property card.

2. **Tax Bill and Receipt Download:**
   - Navigate to county tax websites.
   - Search using the same TMS.
   - Save tax bills and receipts as PDFs.

3. **Deed Document Extraction:**
   - Retrieve Book/Page/Year entries from property card data.
   - Navigate to the deed search page.
   - Input Book and Page numbers.
   - Handle checkbox agreements.
   - Download deed PDFs after clicking the "View" button.

4. **Handling Bot Protection:**
   - Uses residential proxies to prevent IP blocking.
   - Detects CAPTCHA challenges and pauses for manual input.
   - Uses human-like mouse movements and delays to mimic real users.

---

## Improvements and Future Work

- **Automated CAPTCHA Solving:** Integrate third-party CAPTCHA solving services (e.g., 2Captcha) to fully automate scraping without manual intervention.
- **Proxy Rotation:** Dynamically rotate proxies to avoid IP bans and distribute request load.
- **Parallelization:** Enable concurrent scraping of multiple TMS numbers to improve throughput.
- **Error Recovery:** Implement retry mechanisms and robust exception handling for transient failures.
- **Expand Coverage:** Extend support to additional counties or different types of property documents.
- **Monitoring Dashboard:** Build a web-based UI for real-time status updates, logs, and error alerts.
- **Data Export:** Support exporting extracted metadata to CSV, JSON, or databases.
- **Scheduling:** Automate runs using cron jobs or task schedulers for periodic scraping.

---

## Time Spent

The project took approximately **30-40 hours**, including:

- Initial research on scraping restrictions and anti-bot mechanisms.
- Development of Playwright scripts and proxy integration.
- Debugging page navigation issues and CAPTCHA interruptions.
- Testing with multiple TMS examples.
- Writing documentation and packaging the project for delivery.

---

## Getting Started

### Prerequisites

- Python 3.9 or higher  
- Playwright Python library  
- Access to Zyte Smart Proxy Manager with a valid API key  

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/real_estate_scraper.git
   cd real_estate_scraper
