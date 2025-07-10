# TestVault Alerts

This repository scrapes drug test results from TestVault and can alert via email when new results are available, including
a list of clients for whom one or more individual drugs were present. It relies on Selenium, OCR utilities and other third‑party tools.

This branch is set up for deployment on MacOS and Windows devices.

The first time this program runs, it will likely take 5 to 10 minutes to download and search through all results. If run
regularly (see "Automatic Scheduling" below), each run will take less than a minute. The program can always run in the background.

# Plug-and-Play Setup
## MacOS
Download `MacExecutable.zip` from this repository and unzip it. A `testvault-alerts` folder
will appear containing the `testvault-alert-sender` executable and an
`environment.txt.template` file.

1. Inside `testvault-alerts` copy `environment.txt.template` to `environment.txt` and edit
   it with your SMTP and TestVault credentials (see the "Environment Setup" section below for more information):
   ```bash
   cp environment.txt.template environment.txt
   ```
2. Double click `testvault-alert-sender` to run. On first launch a file picker will
   ask where downloaded PDFs should be saved. The location is remembered for
   future runs. Run the executable from the command line with the `--reset-config` flag to choose a new folder.

# Environment Setup

1. Copy `environment.txt.template` to `environment.txt` in the repository root
   (or the folder with the executable):
   ```bash
   cp environment.txt.template environment.txt
   ```
2. Edit `environment.txt` and fill in the SMTP and TestVault credentials:
    - `SMTP_USER` and `SMTP_PASS` – email account used to send notifications.
        - The password must not be one that is set up for two-factor authentication, so you'll likely need to create an
          "app password" through your email provider.
    - `TESTVAULT_USER` and `TESTVAULT_PASS` – TestVault login credentials.
    - `CLIENTS_LIST_URL` – your house's client list page URL in TestVault.
        - To get this URL, log in to TestVault, click on "Groups" and then click on the link to your house. Then copy your
          browser's current URL.
    - Optional `SEND_TO` – email address that should receive the alerts.


# Manual Setup

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

## Running The Program
By design, alertSender.py should be run for full functionality.

If run individually, TestVaultScraper.py scrapes TestVault for new results and downloads any new results to your Downloads
folder.

alertSender.py remembers the download folder you pick the first time it runs.
Use the `--reset-config` flag to choose a new folder. 

When alertSender.py is run it downloads new results, checks each PDF for positive
results and then emails SEND_TO with a summary of any clients whose tests were
positive for one or more drugs.

# Automatic Scheduling
I suggest using launchd (on MacOS) or Task Scheduler (on Windows) to run alertSender.py at scheduled times or intervals.
Allowing alertSender/testvault-alert-sender to run automatically once or twice a day results in an email notification
whenever new results are uploaded without any user interaction. Emails also list the chosen download directory and the 
clients with positive results, expediting the process of checking for concerning results
