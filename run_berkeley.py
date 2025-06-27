import os
from playwright.sync_api import sync_playwright
from berkeley_agent import BerkeleyAgent

test_tms = "2340601038"
output_folder = os.path.join(".", "output", "Berkeley", test_tms)

print("Starting Berkeley scraper...")

with sync_playwright() as p:
    agent = BerkeleyAgent(p, headless=False)

    print("📄 Saving property card...")
    book_page_years = agent.save_property_card_pdf(test_tms, output_folder)

    print("💰 Saving tax bill and receipt...")
    agent.save_tax_documents(test_tms, output_folder)

    print("📘 Saving deed documents...")
    for book, page, year in book_page_years:
        agent.save_deed_pdf(book, page, year, output_folder)

    agent.close()

print("Done.")
