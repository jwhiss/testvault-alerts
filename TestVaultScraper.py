"""
TestVaultScraper.py: Downloads new UA results and provides utilities for checking positives.
Copyright (C) 2025 Joel Whissel (JoelJWhissel@gmail.com)

This program is free software: you can redistribute it and/or modify it under the
terms of the GNU Affero General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along
with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
import os, re, requests, csv
import logging
from pdfminer.high_level import extract_pages  # for machine-readable PDFs
from pdfminer.layout import LTTextContainer  # for machine-readable PDFs
from pathlib import Path

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from config import get_appdata_path, get_config_value

# logging setup
logging.getLogger("pdfminer").setLevel(logging.ERROR)


def create_headless_chrome_driver():
    """Create and return a headless Chrome WebDriver instance."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")            # bypass GPU bits
    options.add_argument("--no-sandbox")             # skip the Chrome sandbox
    options.add_argument("--disable-dev-shm-usage")  # avoid shared-memory errors
    return webdriver.Chrome(options=options)


def load_testvault_credentials():
    """Load TestVault credentials/URLs from config and validate presence."""
    username = get_config_value("testvault_user")
    password = get_config_value("testvault_pass")
    clients_url = get_config_value("clients_list_url")
    if not (username and password and clients_url):
        raise RuntimeError(
            "TestVault credentials are missing. Run alertSender and input "
            "TestVault email, password, and clients list URL."
        )
    return username, password, clients_url


def login_to_testvault(driver, clients_url, username, password, timeout_seconds=5):
    """Log into TestVault using Selenium and raise if login fails."""
    driver.get(clients_url)
    try:
        driver.find_element(By.ID, "id_email").send_keys(username)
        driver.find_element(By.ID, "id_password").send_keys(password)
        driver.find_element(By.CLASS_NAME, "btn").click()
        WebDriverWait(driver, timeout_seconds).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/organizations/logout/']"))
        )
    except Exception:
        raise RuntimeError(
            "Testvault login failed – check testvault credentials in config.json"
        )


def build_requests_session_from_driver(driver):
    """Create a requests.Session populated with Selenium cookies."""
    sess = requests.Session()
    for c in driver.get_cookies():
        sess.cookies.set(c["name"], c["value"])
    return sess


def snapshot_company_links(driver):
    """Snapshot organization links before navigation so elements don't stale."""
    company_links = []
    for element in driver.find_elements(By.CSS_SELECTOR, "a[href*='person/list/']"):
        href = element.get_attribute("href")
        text = element.text.strip()
        if href:
            company_links.append((href, text))
    return company_links


def parse_first_last(display_name):
    """Parse a display name into (first, last) using the first two tokens."""
    parts = [p for p in display_name.split(" ") if p]
    first = parts[0] if len(parts) >= 1 else ""
    last = parts[1] if len(parts) >= 2 else ""
    return first, last


def collect_client_ids(driver, company_links):
    """Visit each company page and return mapping of client_id -> [last, first]."""
    clients = {}
    for company_url, name in company_links:
        first, last = parse_first_last(name)
        driver.get(company_url)

        for item in driver.find_elements(By.CSS_SELECTOR, "a[href*='person/update/']"):
            client_url = item.get_attribute("href")
            m = re.search(r"/person/update/(\d+)", client_url)
            if not m:
                continue
            text = item.text.strip()
            if text.lower() == "my account":
                continue
            cid = m.group(1)
            clients[cid] = [last, first]
            break
    return clients


def load_prior_tests(priors_csv_path):
    """Load previously-downloaded tests from CSV into a set of (name, date)."""
    prior = set()
    if os.path.exists(priors_csv_path):
        with open(priors_csv_path, newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                prior.add((row[0], row[1]))
    return prior


def base_url_from_clients_url(clients_url):
    """Derive the base URL from the clients list URL."""
    m = re.search(r"(.*)/list/$", clients_url)
    if not m:
        raise RuntimeError(f"No base URL found in {clients_url}")
    return m.group(1)


def extract_test_date_from_title(pdf_title):
    """Extract MMDDYYYY date token from a PDF title (returns raw token or None)."""
    m = re.search(r"(\d{8})\.pdf$", pdf_title or "")
    return m.group(1) if m else None


def build_pdf_path(download_dir, first_name, last_name, collection_date_formatted):
    """Build a stable PDF file path for a downloaded result."""
    os.makedirs(download_dir, exist_ok=True)
    return os.path.join(
        download_dir,
        f"{first_name + last_name[0]}" + collection_date_formatted[4:10] + ".pdf",
    )


def download_pdf_to_path(sess, pdf_url, pdf_path, chunk_size=256 * 1024):
    """Download a PDF via requests and write it to disk."""
    resp = sess.get(pdf_url, stream=True)
    resp.raise_for_status()
    with open(pdf_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size):
            f.write(chunk)


def append_prior_test(priors_csv_path, full_name, test_date):
    """Append a downloaded test record to the priors CSV."""
    with open(priors_csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([full_name, test_date])


class Test:
    """
    One UA Test with client name, collection date, download date, path
    """

    def __init__(self, pdf_path: str, client_name="", collection_date="",
                 download_date=""):
        self.pdf_path = pdf_path
        self.client = client_name
        self.collection_date = collection_date
        self.download_date = download_date

    def extract_text(self):
        """
        For PDFs with machine-readable text, returns full text
        """
        full_text = []
        for page_layout in extract_pages(self.pdf_path):
            page_text = []
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    page_text.append(element.get_text())
            full_text.append("".join(page_text))
        return "\n".join(full_text)

    def is_positive(self, keywords=("Inconsistent Result","reportable","above"), min_chars=500):
        """Check if the PDF at pdf_path contains any of the keywords.
        Try extract_text and if len > min_chars, check for each keyword.
        Else print that PDF could not be read
        """
        pdf_name = os.path.basename(self.pdf_path)
        found = False
        method = "Miner"
        mined_text = self.extract_text()
        if len(mined_text.strip()) > min_chars: # PDF is machine-readable
            for key in keywords:
                if key in mined_text:
                    found = True
                    print(f"{method} → Found “{key}” in {pdf_name}")
        else:
            print(f"Could not read {pdf_name} - check manually")
            return None
        if not found:
            print(f"{method} — No {keywords} in {pdf_name}")
        return found


def download_results(dates_dir, data_dir=Path(__file__).resolve().parent):
    """Checks TestVault and downloads new results to dates_dir/TODAY."""
    PRIORS_CSV = os.path.join(data_dir, "priorTests.csv")
    TODAY_FORMATTED = datetime.today().strftime("%Y-%m-%d")
    START_FORMATTED = datetime.now().strftime("%H:%M:%S")

    print(f"{TODAY_FORMATTED} {START_FORMATTED}: Running TestVaultScraper.py")

    driver = None
    try:
        driver = create_headless_chrome_driver()

        username, password, clients_url = load_testvault_credentials()
        download_dir = os.path.join(dates_dir, f"{TODAY_FORMATTED}")

        login_to_testvault(driver, clients_url, username, password)
        sess = build_requests_session_from_driver(driver)

        company_links = snapshot_company_links(driver)
        clients = collect_client_ids(driver, company_links)
        print("Found client IDs:", clients)

        prior = load_prior_tests(PRIORS_CSV)
        base_url = base_url_from_clients_url(clients_url)

        new_results = set()
        for cid, names in clients.items():
            driver.get(f"{base_url}/documents/{cid}/")
            full_name = names[1] + " " + names[0]
            print(f"Checking results for {full_name}")

            try:
                pdf_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/documents/download/']")
                print("Found PDFs for: ", end="")

                for link in pdf_links:
                    pdf_url = link.get_attribute("href")
                    pdf_title = link.get_attribute("title")

                    m = re.search(r"(\d{8})\.pdf$", pdf_title or "")
                    test_date = m.group(1) if m else None
                    if not test_date:
                        logging.warning("No date found in %s - skipping", pdf_title)
                        continue

                    test_date_formatted = datetime.strptime(test_date, "%m%d%Y").strftime("%Y-%m-%d")
                    test_id = (full_name, test_date)

                    if test_id not in prior:
                        pdf_path = build_pdf_path(
                            download_dir,
                            first_name=names[1],
                            last_name=names[0],
                            collection_date_formatted=test_date_formatted,
                        )
                        download_pdf_to_path(sess, pdf_url, pdf_path)

                        print(f"{test_date_formatted} (new)", end=", ")
                        new_results.add(Test(pdf_path, full_name, test_date_formatted, TODAY_FORMATTED))

                        append_prior_test(PRIORS_CSV, full_name, test_date)
                        prior.add(test_id)
                    else:
                        print(f"{test_date_formatted} (already recorded, ending search)")
                        break

                print(f"Finished checking {len(pdf_links)} PDFs for {full_name}\n")
            except Exception as e:
                print(f"No results for {full_name}: {e}\n")

        print(
            f"\nFinished checking {len(clients)} clients and downloaded {len(new_results)} new results\n"
        )
        return new_results
    finally:
        if driver is not None:
            driver.quit()


def list_positives(pdfs_dir):
    """
    Create Tests for each PDF in pdfs_dir, then 
    return a set of the Tests with positive results
    """
    base = Path(pdfs_dir)
    p_list = ""
    for pdf_path in base.glob("*.pdf"):
        current = Test(pdf_path)
        if current.is_positive():
            p_list += os.path.basename(pdf_path)
    return p_list

if __name__ == "__main__":
    try:
        download_results(Path.home() / "Downloads")
    except Exception:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)s: %(message)s')
        logging.exception("TestVaultScraper.py terminated with an error")
        sys.exit(1)
    print("TestVaultScraper is main - no email sent")
