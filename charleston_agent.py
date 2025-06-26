import os
from playwright.sync_api import TimeoutError, Error
from urllib.parse import urlparse, parse_qs

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

        account_number = None
        try:
            self.page.wait_for_selector('a[title="Tax Info"]', timeout=10000)
            self.page.click('a[title="Tax Info"]')
            self.page.wait_for_url("**/AccountSummary.aspx**", timeout=15000)
            self.page.wait_for_load_state("load")
            self.page.wait_for_timeout(2000)

            url = self.page.url
            print(f"🔗 Tax Info URL: {url}")

            if "AccountSummary.aspx" in url and "p=" in url and "&a=" in url:
                parsed_url = urlparse(url)
                params = parse_qs(parsed_url.query)
                tms_number = params.get("p", [tms])[0]
                account_number = params.get("a", [None])[0]

                tax_pdf_path = os.path.join(output_folder, f"{tms_number}_Tax_Info.pdf")
                try:
                    self.page.wait_for_selector('a[title="Print Page"], cr-button[role="button"]', timeout=10000)
                    with self.context.expect_page(timeout=10000) as print_page_info:
                        print_link = self.page.query_selector('a[title="Print Page"]')
                        if print_link:
                            print_link.click()
                        else:
                            print_button = self.page.query_selector('cr-button[role="button"]')
                            if print_button:
                                print_button.click()
                            else:
                                raise Exception("Print button/link not found")
                    print_page = print_page_info.value
                    print_page.wait_for_load_state("load")
                    print_page.wait_for_timeout(2000)
                    print_page.pdf(path=tax_pdf_path)
                    print_page.close()
                    print(f"✅ Saved Tax Info PDF from print preview at {tax_pdf_path}")
                except TimeoutError:
                    self.page.pdf(path=tax_pdf_path)
                    print(f"✅ Saved Tax Info PDF from current page at {tax_pdf_path}")
            else:
                print(f"⚠️ Unexpected Tax Info URL format: {url}")
        except Exception as e:
            print(f"❌ Error while handling Tax Info: {e}")

        return book_page_pairs, account_number

    def save_deed_pdf(self, book, page_num, output_folder):
        # ✅ Use isolated context to avoid CAPTCHA blocks
        isolated_context = self.browser.new_context()
        page = isolated_context.new_page()

        try:
            page.goto("https://www.charlestoncounty.org/departments/rod/ds-DMBookandPage.php", timeout=60000)
            page.fill('input#booknumber', book)
            page.fill('input#pagenumber', page_num)

            checkbox = page.query_selector('input[name="agreelegal"]')
            if checkbox and checkbox.get_attribute("type") == "checkbox":
                checkbox.check()
            else:
                print(f"⚠️ Checkbox not found or not clickable for Book {book} Page {page_num}")

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
                print(f"⚠️ Could not scroll to View link for Book {book} Page {page_num}")

            with isolated_context.expect_page() as new_page_info:
                view_link.click()

            pdf_page = new_page_info.value
            pdf_page.wait_for_load_state("load")
            pdf_page.wait_for_load_state("networkidle")
            pdf_page.wait_for_timeout(2000)

            try:
                pdf_page.wait_for_selector("canvas", timeout=15000)
                print(f"🖼️ PDF canvas found for Book {book} Page {page_num}")
            except TimeoutError:
                print(f"⚠️ No canvas, proceeding anyway for Book {book} Page {page_num}")

            frame = None
            try:
                frame = pdf_page.query_selector('iframe[src*=".pdf"], embed[type="application/pdf"]')
            except Error as e:
                print(f"⚠️ Error looking for iframe/embed: {e}")

            save_path = os.path.join(output_folder, f"DB_{book}_{page_num}.pdf")
            os.makedirs(output_folder, exist_ok=True)

            if frame:
                pdf_url = frame.get_attribute("src")
                if pdf_url and not pdf_url.startswith("about:blank"):
                    pdf_page.goto(pdf_url)
                    pdf_page.wait_for_load_state("networkidle")
                    pdf_page.wait_for_timeout(2000)
                    pdf_page.pdf(path=save_path)
                    print(f"✅ Saved deed PDF from iframe: {save_path}")
                else:
                    pdf_page.pdf(path=save_path)
                    print(f"✅ Saved deed PDF from blank iframe: {save_path}")
            else:
                pdf_page.pdf(path=save_path)
                print(f"✅ Saved deed PDF from main content: {save_path}")

            pdf_page.close()

        except TimeoutError as te:
            print(f"❌ Timeout on Book {book} Page {page_num}: {te}")
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
                print(f"⚠️ Failed to capture screenshot: {ss_e}")
        finally:
            page.close()
            isolated_context.close()

    def close(self):
        self.context.close()
        self.browser.close()
