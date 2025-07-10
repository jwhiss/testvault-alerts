# TestVault Alerts

This repository scrapes drug test results from TestVault and can alert via email when new results are available, including
a list of clients for whom one or more individual drugs were present. It relies on Selenium, OCR utilities and other third‑party tools.

**"Pre-deployment" is not set up for deployment on most devices. Using this branch will require some modifications. 
use the "deployment" branch instead**

## System Requirements

Before running or building the project ensure these system packages are installed:

- **Tesseract OCR** – used to read scanned PDFs.
- **Poppler** – `pdf2image` requires Poppler to convert PDFs to images.
- **Google Chrome** and **ChromeDriver** – Selenium controls Chrome to download results.

Full requirements can be found in requirements.txt, and packages can usually be installed from your system package manager. 
For example, on macOS using Homebrew:

```bash
brew install tesseract poppler
brew install --cask google-chrome chromedriver
```

On Windows, download and install the Tesseract, Poppler and Chrome/ChromeDriver packages and ensure their executables are in your `PATH`.

## Environment Setup

1. Copy `.env.template` to `.env` in the repository root:
   ```bash
   cp .env.template .env
   ```
2. Edit `.env` and fill in the SMTP and TestVault credentials:
    - `SMTP_USER` and `SMTP_PASS` – email account used to send notifications.
    - `TESTVAULT_USER` and `TESTVAULT_PASS` – TestVault login.
    - `CLIENTS_LIST_URL` – your house's client list page URL in TestVault.
    - Optional `SEND_TO` – email address that should receive the alerts.

## Running The Program
By design, alertSender.py should be run for full functionality. 

If run individually, TestVaultScraper.py scrapes TestVault for new results and downloads any new results to **an incorrect folder**

alertSender.py takes one command line argument `--download-dir` with the full path to the directory you would like new tests
to appear in. This directory will also include priorTests.csv (see below), which should not be altered. By default, the
download directory is **incorrect**

When alertSender.py is run, it completes the scrape-and-download process from TestVaultScraper.py, with the download directory
set by command line argument, then checks each PDF for positive results. It then sends an email from SMTP_USER to SEND_TO 
with the number of new results and a list of any clients whose tests were positive for one or more individual drugs.

### Automatic Scheduling
I suggest using launchd (on MacOS) or Task Scheduler (on Windows) to run alertSender.py at scheduled times or intervals.

### priorTests.csv
This file will be automatically generated and stored in the same directory you set for file downloads, or "Downloads" if
no file is added as an argument. 

priorTests.csv keeps track of previously checked UA results, and does not need to be modified.