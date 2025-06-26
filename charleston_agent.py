import os
import time
import random
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright, TimeoutError, Error, expect

def human_delay(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def random_mouse_movement(page):
    for _ in range(random.randint(2, 5)):
        x = random.randint(100, 1000)
        y = random.randint(100, 500)
        page.mouse.move(x, y)
        human_delay(0.1, 0.3)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36",
]

class CharlestonAgent:
    def __init__(self, playwright, headless=False):
        self.playwright = playwright
        self.headless = headless
        self.browser = playwright.chromium.launch(headless=headless, slow_mo=400)
        self.context = self._create_context()
        self.page = self.context.new_page()

    def _create_context(self):
        return self.browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 720},
            locale="en-US",
            accept_downloads=True
        )

    def save_property_card_pdf(self, tms, output_folder):
        page = self.page
        page.goto("https://charlestoncounty.org/online-services.php")
        random_mouse_movement(page)
        page.click("text=Pay Taxes & View Records")
        human_delay()
        page.click("text=Real Property Record Search")
        human_delay()
        page.fill('input[title="PIN"]', tms)
        human_delay()
        page.keyboard.press("Tab")
        page.keyboard.press("Enter")
        page.wait_for_selector('text=View Details')
        human_delay()
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

        account_number = None
        try:
            page.wait_for_selector('a[title="Tax Info"]', timeout=10000)
            page.click('a[title="Tax Info"]')
            page.wait_for_url("**/AccountSummary.aspx**", timeout=15000)
            page.wait_for_load_state("load")
            page.wait_for_timeout(2000)

            url = page.url
            print(f"🔗 Tax Info URL: {url}")

            if "AccountSummary.aspx" in url and "p=" in url and "&a=" in url:
                parsed_url = urlparse(url)
                params = parse_qs(parsed_url.query)
                tms_number = params.get("p", [tms])[0]
                account_number = params.get("a", [None])[0]

                tax_pdf_path = os.path.join(output_folder, f"{tms_number}_Tax_Info.pdf")
                try:
                    page.wait_for_selector('a[title="Print Page"], cr-button[role="button"]', timeout=10000)
                    with self.context.expect_page(timeout=10000) as print_page_info:
                        print_link = page.query_selector('a[title="Print Page"]')
                        if print_link:
                            print_link.click()
                        else:
                            print_button = page.query_selector('cr-button[role="button"]')
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
                    page.pdf(path=tax_pdf_path)
                    print(f"✅ Saved Tax Info PDF from current page at {tax_pdf_path}")
        except Exception as e:
            print(f"❌ Error while handling Tax Info: {e}")

        return book_page_pairs, account_number

    def save_deed_pdf(self, book, page_num, output_folder):
        context = self.browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 720},
            locale="en-US",
            accept_downloads=True,
        )
        page = context.new_page()
        try:
            page.goto("https://www.charlestoncounty.org/departments/rod/ds-DMBookandPage.php", timeout=60000)
            human_delay()
            random_mouse_movement(page)

            page.fill('input#booknumber', book)
            page.fill('input#pagenumber', page_num)
            human_delay()

            checkbox = page.query_selector('input[name="agreelegal"]')
            if checkbox and checkbox.get_attribute("type") == "checkbox":
                if not checkbox.is_checked():
                    checkbox.check()
                human_delay()
            else:
                print(f"⚠️ 'agreelegal' checkbox not found or not a checkbox for Book {book} Page {page_num}")

            # Submit via keyboard to reduce bot detection
            page.keyboard.press("Tab")
            human_delay(0.3, 0.6)
            page.keyboard.press("Enter")

            # Wait and retry for results to load, checking for captcha or table rows
            for attempt in range(5):
                try:
                    # Wait for either table rows or captcha to appear
                    page.wait_for_selector("#myTable tbody tr, [id*=captcha]", timeout=8000)
                    break
                except TimeoutError:
                    print(f"⚠️ Waiting for results attempt {attempt+1} timed out, retrying after scroll...")
                    # Scroll table container explicitly (improve chances view link visible)
                    page.evaluate('document.querySelector("#myTable tbody").scrollTop = document.querySelector("#myTable tbody").scrollHeight')
                    human_delay(1, 2)
            else:
                print("❌ Deed search results did not appear after retries.")
                return

            # Check for CAPTCHA
            if page.query_selector("[id*=captcha]"):
                print(f"⚠️ CAPTCHA detected for Book {book} Page {page_num}. Please solve it manually.")
                captcha_path = os.path.join(output_folder, f"captcha_{book}_{page_num}.png")
                page.screenshot(path=captcha_path)
                print(f"📸 CAPTCHA screenshot saved: {captcha_path}")
                input("▶️ Press Enter after solving CAPTCHA manually...")
                human_delay()

            # Now search rows again
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
                # Save debug info
                os.makedirs(output_folder, exist_ok=True)
                page.screenshot(path=os.path.join(output_folder, f"no_view_link_{book}_{page_num}.png"))
                with open(os.path.join(output_folder, f"no_view_link_{book}_{page_num}.html"), "w", encoding="utf-8") as f:
                    f.write(page.content())
                return

            # Scroll + hover + click view link with retries
            for attempt in range(5):
                if view_link.is_visible() and view_link.is_enabled():
                    view_link.scroll_into_view_if_needed()
                    human_delay(0.8, 1.5)
                    view_link.hover()
                    human_delay(0.5, 1.2)
                    break
                else:
                    print(f"🔄 Waiting for View link visibility... Attempt {attempt + 1}")
                    # Scroll container again to trigger visibility
                    page.evaluate('document.querySelector("#myTable tbody").scrollTop += 100')
                    human_delay(1)
            else:
                print(f"❌ View link never became visible for Book {book} Page {page_num}")
                os.makedirs(output_folder, exist_ok=True)
                page.screenshot(path=os.path.join(output_folder, f"view_link_not_visible_{book}_{page_num}.png"))
                with open(os.path.join(output_folder, f"view_link_not_visible_{book}_{page_num}.html"), "w", encoding="utf-8") as f:
                    f.write(page.content())
                return

            with context.expect_page() as new_page_info:
                view_link.click()

            pdf_page = new_page_info.value
            pdf_page.wait_for_load_state("load")
            pdf_page.wait_for_load_state("networkidle")
            human_delay(2)

            save_path = os.path.join(output_folder, f"DB_{book}_{page_num}.pdf")
            os.makedirs(output_folder, exist_ok=True)

            frame = pdf_page.query_selector('iframe[src*=".pdf"], embed[type="application/pdf"]')
            if frame:
                pdf_url = frame.get_attribute("src")
                if pdf_url and not pdf_url.startswith("about:blank"):
                    pdf_page.goto(pdf_url)
                    pdf_page.wait_for_load_state("networkidle")
                    human_delay(2)
                    pdf_page.pdf(path=save_path)
                    print(f"✅ Saved deed PDF from iframe: {save_path}")
                else:
                    pdf_page.pdf(path=save_path)
                    print(f"✅ Saved deed PDF from blank iframe: {save_path}")
            else:
                pdf_page.pdf(path=save_path)
                print(f"✅ Saved deed PDF from main content: {save_path}")

            pdf_page.close()

        except Exception as e:
            print(f"❌ Error on Book {book} Page {page_num}: {e}")
            error_path = os.path.join(output_folder, f"error_{book}_{page_num}.png")
            page.screenshot(path=error_path)
            print(f"📸 Screenshot saved: {error_path}")
            with open(os.path.join(output_folder, f"error_{book}_{page_num}.html"), "w", encoding="utf-8") as f:
                f.write(page.content())
        finally:
            page.close()
            context.close()

    def close(self):
        self.context.close()
        self.browser.close()
