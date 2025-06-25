import os
from playwright.sync_api import TimeoutError, Error

class CharlestonAgent:
    def __init__(self, playwright, headless=True):
        self.browser = playwright.chromium.launch(headless=headless)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def save_property_card_pdf(self, tms, output_folder):
        self.page.goto("https://charlestoncounty.org/online-services.php")
        self.page.click("text=Pay Taxes & View Records")
        self.page.click("text=Real Property Record Search")
        self.page.fill('input[title="PIN"]', tms)
        self.page.click('button:has-text("Search")')

        self.page.wait_for_selector('text=View Details')
        self.page.click('text=View Details')

        self.page.wait_for_load_state("load")
        self.page.wait_for_timeout(2000)

        book_page_pairs = []
        rows = self.page.query_selector_all("table tr")
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
        self.page.pdf(path=pdf_path)
        print(f"✅ Saved Property Card PDF for TMS {tms} at {pdf_path}")

        return book_page_pairs

    def save_deed_pdf(self, book, page_num, output_folder):
        page = self.context.new_page()
        try:
            page.goto("https://www.charlestoncounty.org/departments/rod/ds-DMBookandPage.php", timeout=60000)

            page.fill('input#booknumber', book)
            page.fill('input#pagenumber', page_num)

            checkbox = page.query_selector('input[name="agreelegal"]')
            if checkbox and checkbox.get_attribute("type") == "checkbox":
                checkbox.check()
            else:
                print(f"⚠️ 'agreelegal' checkbox not found or is not a checkbox for Book {book} Page {page_num}")

            page.click('input[name="send_button"]')
            page.wait_for_selector("#myTable tbody tr", timeout=30000)

            rows = page.query_selector_all("#myTable tbody tr")
            view_link = None
            for row in rows:
                cells = row.query_selector_all("td")
                if len(cells) >= 10:
                    row_book = cells[1].inner_text().strip()
                    row_page = cells[2].inner_text().strip()
                    if row_book == book and row_page == page_num:
                        link = cells[9].query_selector('a')
                        if link and "View" in link.inner_text():
                            view_link = link
                            break

            if not view_link:
                print(f"❌ No View link found for Book {book} Page {page_num}")
                return

            try:
                view_link.scroll_into_view_if_needed(timeout=10000)
            except TimeoutError:
                print(f"⚠️ Timeout scrolling view link for Book {book} Page {page_num}")

            with self.context.expect_page() as new_page_info:
                view_link.click()

            pdf_page = new_page_info.value

            pdf_page.wait_for_load_state("load")
            pdf_page.wait_for_load_state("networkidle")
            pdf_page.wait_for_timeout(2000)

            try:
                pdf_page.wait_for_selector("canvas", timeout=15000)
                print(f"🖼️ PDF canvas found for Book {book} Page {page_num}")
            except TimeoutError:
                print(f"⚠️ PDF canvas not found, proceeding anyway for Book {book} Page {page_num}")

            frame = None
            try:
                frame = pdf_page.query_selector('iframe[src*=".pdf"], embed[type="application/pdf"]')
            except Error as e:
                print(f"⚠️ Error querying for PDF frame: {e}")

            save_path = os.path.join(output_folder, f"DB_{book}_{page_num}.pdf")
            os.makedirs(output_folder, exist_ok=True)

            if frame:
                pdf_url = frame.get_attribute("src")
                if pdf_url and not pdf_url.startswith("about:blank"):
                    pdf_page.goto(pdf_url)
                    pdf_page.wait_for_load_state("networkidle")
                    pdf_page.wait_for_timeout(2000)
                    pdf_page.pdf(path=save_path)
                    print(f"✅ Saved deed PDF from iframe src: {save_path}")
                else:
                    pdf_page.pdf(path=save_path)
                    print(f"✅ Saved deed PDF directly from page (iframe src blank): {save_path}")
            else:
                url = pdf_page.url.lower()
                if pdf_page.url.endswith('.pdf') or ('pdf' in url):
                    pdf_page.pdf(path=save_path)
                    print(f"✅ Saved deed PDF directly: {save_path}")
                else:
                    pdf_page.pdf(path=save_path)
                    print(f"✅ Saved deed PDF directly from page (no iframe): {save_path}")

            pdf_page.close()

        except TimeoutError as te:
            print(f"❌ Timeout error on Book {book} Page {page_num}: {te}")
            error_path = os.path.join(output_folder, f"error_{book}_{page_num}.png")
            page.screenshot(path=error_path)
            print(f"📸 Screenshot saved: {error_path}")
        except Exception as e:
            print(f"❌ Error processing Book {book} Page {page_num}: {e}")
            error_path = os.path.join(output_folder, f"error_{book}_{page_num}.png")
            try:
                page.screenshot(path=error_path)
                print(f"📸 Screenshot saved: {error_path}")
            except Exception as ss_e:
                print(f"⚠️ Failed to take screenshot: {ss_e}")
        finally:
            page.close()

    def close(self):
        self.context.close()
        self.browser.close()
