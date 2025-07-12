"""
alertSender.py: Downloads new UA results, checks for positives, and sends an
email with a list of new and positive results.
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
import time, os, re, requests, csv
import logging
import pytesseract  # for scanned PDFs
from pdf2image import convert_from_path  # for scanned PDFs
from pdfminer.high_level import extract_pages  # for machine-readable PDFs
from pdfminer.layout import LTTextContainer  # for machine-readable PDFs
from pathlib import Path

from config import get_appdata_path, get_config_value

# logging setup
logging.getLogger("pdfminer").setLevel(logging.ERROR)

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

    def is_positive(self, keyword="above", min_chars=500):
        """Check if the PDF at pdf_path contains the keyword.
        Try extract_text and if len > min_chars, check for 'keyword'.
        Else convert each page of pdf_path into an image, OCR it with 
        Tesseract, and return True if 'keyword' is found.
        """
        found = False
        method = "Miner"
        mined_text = self.extract_text()
        if len(mined_text.strip()) > min_chars: # PDF is machine-readable
            if keyword in mined_text.lower():
                found = True
                print(f"{method} → Found “{keyword}” in "
                      + os.path.basename(self.pdf_path))
        else: # backup: use OCR
            method = "OCR  "
            pages = convert_from_path(self.pdf_path, dpi=300)
            for img in pages:
                text = pytesseract.image_to_string(img)
                if keyword.lower() in text.lower():
                    found = True
                    print(f"{method} → Found “{keyword}” in "
                          + os.path.basename(self.pdf_path))
                    break # untested change from 'continue'
        if not found:
            print(f"{method} — No “{keyword}” in {os.path.basename(self.pdf_path)}")
        return found

def download_results(dates_dir, data_dir=Path(__file__).resolve().parent):
    """Checks TestVault and downloads new results to dates_dir/TODAY"""
    # constants
    PRIORS_CSV = os.path.join(data_dir, "priorTests.csv")
    TODAY_FORMATTED = datetime.today().strftime("%Y-%m-%d")
    START_FORMATTED = datetime.now().strftime("%H:%M:%S")
    if getattr(sys, 'frozen', False): # Running as a bundled .exe
        BASE_DIR = Path(sys.executable).resolve().parent
    else: # Running as a .py script
        BASE_DIR = Path(__file__).resolve().parent

    print(f"{TODAY_FORMATTED} {START_FORMATTED}: Running TestVaultScraper.py")
    
    # obtain credentials from config
    username = get_config_value("testvault_user")
    password = get_config_value("testvault_pass")
    clients_url = get_config_value("clients_list_url")
    if not (username and password and clients_url):
        raise RuntimeError("TestVault credentials are missing. Run alertSender and input "
                           "TestVault email, password, and clients list URL.")

    # set directory for PDF downloads
    download_dir = os.path.join(dates_dir, f"{TODAY_FORMATTED}")

    # set up headless Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options)
    
    # log in
    driver.get(clients_url)
    try:
        driver.find_element(By.ID, "id_email").send_keys(username)
        driver.find_element(By.ID, "id_password").send_keys(password)
        driver.find_element(By.CLASS_NAME, "btn").click()
        time.sleep(2)  # wait for redirect
    except:
        print("Already logged in (or failed)")
    finally:
        # simple check: does the logout button now exist?
        if not driver.find_elements(By.CSS_SELECTOR, "a[href*='/organizations/logout/']"):
            raise RuntimeError(
                "Testvault login failed – check testvault credentials in config.json"
            )
    
    # Transfer cookie to stay logged in for PDF download:
    sess = requests.Session()
    for c in driver.get_cookies():
        sess.cookies.set(c['name'], c['value'])
    
    # grab all links that point to a client document page and regex out  ID, get text fields
    clients = {} # id -> [last, first]
    for element in driver.find_elements(By.CSS_SELECTOR, "a[href*='person/update/']"):
        client_url = element.get_attribute("href")
        m = re.search(r"/person/update/(\d+)/", client_url)
        
        if not m:
            continue
        cid = m.group(1)
        text = element.text.strip()
        if text.lower() == "edit" or "":
            continue
        clients.setdefault(cid, []).append(text)
    
    print("Found client IDs:", clients)
    
    # Load what’s already been downloaded
    prior = set()
    if os.path.exists(PRIORS_CSV):
        with open(PRIORS_CSV, newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                # row[0] is cid, row[1] is test_date
                prior.add((row[0], row[1]))

    # determine base URL for client-documents pages
    m = re.search(r"(.*)/list/$", clients_url)
    if not m:
        raise RuntimeError(f"No base URL found in {clients_url}")
    base_url = m.group(1)

    new_results = set() # create set for new results (Test)
    for cid, names in clients.items():
        # 1) navigate to client page
        driver.get(f"{base_url}/documents/{cid}/")
        full_name = names[1] + " " + names[0]
        print(f"Checking results for {full_name}")
        try:
            # find PDF elements
            pdf_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/documents/download/']")
            print("Found PDFs for: ", end="")
            for link in pdf_links:
                pdf_url = link.get_attribute("href")
                pdf_title = link.get_attribute("title")
                m = re.search(r"(\d{8})\.pdf$", pdf_title)
                if m:
                    test_date = m.group(1)
                else:
                    logging.warning("No date found in %s - skipping", pdf_title)
                    continue
                test_date_formatted = datetime.strptime(test_date, "%m%d%Y").strftime("%Y-%m-%d") # for collection date folders
                test_id = (full_name, test_date)
                
                # Download new test PDFs and add them to PRIOR_CSV
                is_new = test_id not in prior
                if is_new:
                    
                    # download PDF file, new dir if none yet
                    os.makedirs(download_dir, exist_ok=True)
                    pdf_path = os.path.join(download_dir, f"{names[1] + names[0][0]}"
                                            + test_date_formatted[4:10] + ".pdf")
                    resp = sess.get(pdf_url, stream=True)
                    resp.raise_for_status()
                    
                    # write out the PDF
                    with open(pdf_path, "wb") as f:
                        for chunk in resp.iter_content(1024):
                            f.write(chunk)
                    print(f"{test_date_formatted} (new)", end=", ")
                    new_results.add(Test(pdf_path, full_name, test_date_formatted,
                                         TODAY_FORMATTED))
                    
                    # then record it:
                    with open(PRIORS_CSV, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([full_name, test_date])
                    prior.add(test_id)
                else:
                    print(f"{test_date_formatted} (already recorded, ending search)")
                    break
            print(f"Finished checking {len(pdf_links)} PDFs for {full_name}\n")
        except Exception as e:
            print(f"No results for {full_name}: {e}\n")
            
    driver.quit()
    print(f"\nFinished checking {len(clients)} clients and downloaded {len(new_results)} new results\n")
    
    return new_results

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
