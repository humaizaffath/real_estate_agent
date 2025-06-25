from playwright.sync_api import sync_playwright
from charleston_agent import CharlestonAgent

if __name__ == "__main__":
    test_tms = "5590200072"
    output_folder = f"./output/Charleston/{test_tms}"

    with sync_playwright() as p:
        agent = CharlestonAgent(p, headless=False)

        print("Starting to save property card PDF...")
        book_page_pairs = agent.save_property_card_pdf(test_tms, output_folder)

        print("Starting to save deed PDFs...")
        for book, page_num in book_page_pairs:
            agent.save_deed_pdf(book, page_num, output_folder)

        agent.close()

    print("All done.")
