from playwright.sync_api import sync_playwright
import os

def save_property_card_pdf(tms, output_folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # show browser
        page = browser.new_page()
        
        # 1. Go to Charleston County online services page
        page.goto("https://charlestoncounty.org/online-services.php")
        
        # 2. Click "Pay Taxes & View Records"
        page.click("text=Pay Taxes & View Records")
        
        # 3. Click "Real Property Record Search"
        page.click("text=Real Property Record Search")
        
        # 4. Enter TMS in PIN field (no dashes)
        page.fill('input[title="PIN"]', tms)
        
        # 5. Click Search button
        page.click('button:has-text("Search")')
        
        # 6. Click "View Details"
        page.wait_for_selector('text=View Details')
        page.click('text=View Details')
        
        # 7. Wait for the property details page to fully load
        page.wait_for_load_state("load")

        # 7.5 Extract Book and Page numbers from transaction table
        book_page_pairs = []
        rows = page.query_selector_all("tr")

        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 2:
                book = cells[0].inner_text().strip()
                page_num = cells[1].inner_text().strip()
                if book and page_num and book.isdigit():
                    book_page_pairs.append((book, page_num))

        print("📘 Found Book/Page pairs:", book_page_pairs)

        # 8. Save property card page as PDF
        os.makedirs(output_folder, exist_ok=True)
        pdf_path = os.path.join(output_folder, f"{tms}_Property_Card.pdf")
        page.pdf(path=pdf_path)

        print(f"✅ Saved Property Card PDF for TMS {tms} at {pdf_path}")

        browser.close()
