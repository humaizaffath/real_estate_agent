from playwright.sync_api import sync_playwright
from charleston_agent import CharlestonAgent
import os

test_tms = "5590200072"
output_folder = os.path.join(".", "output", "Charleston", test_tms)

with sync_playwright() as p:
    agent = CharlestonAgent(p, headless=False)

    print("Starting to save property card PDF...")
    book_page_pairs, account_number = agent.save_property_card_pdf(test_tms, output_folder)

    print("Saving deed PDFs...")
    for book, page in book_page_pairs:
        agent.save_deed_pdf(book, page, output_folder)

    agent.close()
