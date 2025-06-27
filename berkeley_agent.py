import os
import time
import random
from playwright.sync_api import sync_playwright

API_KEY = ""  # your Zyte API key

def human_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

class BerkeleyAgent:
    def __init__(self, playwright, headless=False):
        proxy_server = "http://proxy.zyte.com:8011"

        self.context = playwright.chromium.launch_persistent_context(
            user_data_dir="./userdata",
            headless=headless,
            slow_mo=100,
            viewport={'width': 1280, 'height': 720},
            accept_downloads=True,
            proxy={
                "server": proxy_server,
                "username": API_KEY,
                "password": API_KEY,
            },
            ignore_https_errors=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            java_script_enabled=True,
        )
        self.page = self.context.new_page()
        self.page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://assessor.berkeleycountysc.gov/prop_card_search.php"
        })

    def save_property_card_pdf(self, tms, output_folder):
        url = f"https://assessor.berkeleycountysc.gov/property_card.php?tms={tms}"
        print(f"🌐 Navigating to property card page: {url}")
        self.page.goto(url, timeout=60000)
        human_delay()
        os.makedirs(output_folder, exist_ok=True)
        prop_card_path = os.path.join(output_folder, f"{tms}_Property_Card.pdf")
        self.page.pdf(path=prop_card_path)
        print(f"Saved Property Card for {tms} at {prop_card_path}")

    def close(self):
        self.context.close()

if __name__ == "__main__":
    test_tms = "2340601038"
    output_folder = os.path.join(".", "output", "Berkeley", test_tms)

    with sync_playwright() as p:
        print("Starting Berkeley scraper...")
        agent = BerkeleyAgent(p, headless=False)
        agent.save_property_card_pdf(test_tms, output_folder)
        agent.close()
        print("Done.")
