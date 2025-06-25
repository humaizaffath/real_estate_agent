from playwright.sync_api import sync_playwright
import os


def save_property_card_pdf(tms, output_folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://charlestoncounty.org/online-services.php")
        page.click("text=Pay Taxes & View Records")
        page.click("text=Real Property Record Search")
        page.fill('input[title="PIN"]', tms)
        page.click('button:has-text("Search")')

        page.wait_for_selector('text=View Details')
        page.click('text=View Details')

        page.wait_for_load_state("load")
        page.wait_for_timeout(2000)

        book_page_pairs = []
        rows = page.query_selector_all("table tr")
        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 2:
                book = cells[0].inner_text().strip()
                page_num = cells[1].inner_text().strip()
                if book.isdigit() and page_num:
                    book_page_pairs.append((book, page_num))

        print("📘 Found Book/Page pairs:", book_page_pairs)

        os.makedirs(output_folder, exist_ok=True)
        pdf_path = os.path.join(output_folder, f"{tms}_Property_Card.pdf")
        page.pdf(path=pdf_path)
        print(f"✅ Saved Property Card PDF for TMS {tms} at {pdf_path}")

        browser.close()
        return book_page_pairs


def save_deed_pdf(book, page_num, output_folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Step 1: Navigate to page
            page.goto("https://www.charlestoncounty.org/departments/rod/ds-DMBookandPage.php", timeout=60000)

            # Step 2: CAPTCHA check
            if page.query_selector("div#recaptcha"):
                print("⚠️ CAPTCHA detected. Please solve manually in browser. Waiting 30s...")
                page.wait_for_timeout(30000)

            # Step 3: Fill and submit form
            page.fill('input#booknumber', book)
            page.fill('input#pagenumber', page_num)
            page.check('input[name="agreelegal"]')
            page.click('input[name="send_button"]')

            # Step 4: Wait for result rows
            try:
                page.wait_for_selector("#myTable tbody tr", timeout=30000)
            except:
                raise Exception("❌ Results table not found — possibly CAPTCHA or form error.")

            # Step 5: Locate View link
            view_link = None
            rows = page.query_selector_all("#myTable tbody tr")

            for row in rows:
                cells = row.query_selector_all("td")
                if len(cells) >= 10:
                    row_book = cells[1].inner_text().strip()
                    row_page = cells[2].inner_text().strip()
                    if row_book == book and row_page == page_num:
                        link = cells[9].query_selector('a:has-text("View")')
                        if link:
                            view_link = link
                            break

            if not view_link:
                print(f"❌ No View link found for Book {book} Page {page_num}")
                return

            # Step 6: Open the new PDF tab
            with context.expect_page() as new_page_info:
                view_link.click()
            pdf_page = new_page_info.value

            pdf_page.wait_for_load_state("networkidle")
            pdf_page.wait_for_timeout(3000)

            # Step 7: Save the PDF
            os.makedirs(output_folder, exist_ok=True)
            save_path = os.path.join(output_folder, f"DB_{book}_{page_num}.pdf")

            # Step 8: Detect PDF and save accordingly
            if pdf_page.url.endswith(".pdf"):
                pdf_page.pdf(path=save_path)
            else:
                # Try iframe or embed
                frame = pdf_page.query_selector('iframe[src*=".pdf"], embed[type="application/pdf"]')
                if frame:
                    pdf_url = frame.get_attribute("src")
                    if pdf_url:
                        pdf_page.goto(pdf_url, wait_until="load")
                        pdf_page.wait_for_timeout(3000)
                        pdf_page.pdf(path=save_path)
                    else:
                        pdf_page.pdf(path=save_path, format="A4", print_background=True)
                else:
                    # Fallback save
                    pdf_page.pdf(path=save_path, format="A4", print_background=True)

            print(f"✅ Saved deed PDF: {save_path}")
            pdf_page.close()

        except Exception as e:
            print(f"❌ Error processing Book {book} Page {page_num}: {str(e)}")
            error_path = os.path.join(output_folder, f"error_{book}_{page_num}.png")
            page.screenshot(path=error_path)
            print(f"📸 Screenshot saved: {error_path}")
        finally:
            context.close()
            browser.close()
