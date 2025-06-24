from playwright.sync_api import sync_playwright
import os

def save_property_card_pdf(tms, output_folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # open browser visibly for debugging
        page = browser.new_page()
        
        # 1. Go to main page
        page.goto("https://charlestoncounty.org/online-services.php")
        
        # 2. Click "Pay Taxes & View Records"
        page.click("text=Pay Taxes & View Records")
        
        # 3. Click "Real Property Record Search"
        page.click("text=Real Property Record Search")
        
        # 4. Enter TMS in PIN field (no dashes)
        page.fill('input[title="PIN"]', tms)  # <-- Updated selector here
        
        # 5. Click Search button
        page.click('button:has-text("Search")')
        
        # 6. Wait for 'View Details' link to appear and click it
        page.wait_for_selector('text=View Details')
        page.click('text=View Details')
        
        # 7. Wait for page to load fully
        page.wait_for_load_state("load")

        
        # 8. Save page as PDF
        os.makedirs(output_folder, exist_ok=True)
        pdf_path = os.path.join(output_folder, f"{tms}_Property_Card.pdf")
        page.pdf(path=pdf_path)
        
        print(f"Saved Property Card PDF for TMS {tms} at {pdf_path}")
        
        browser.close()
