# TestVault Alerts

This repository scrapes drug test results from TestVault and can alert via email when new results are available, including
a list of clients for whom one or more individual drugs were present. It relies on Selenium, OCR utilities and other third‑party tools.

This branch is set up for deployment on MacOS and Windows devices.

The first time this program runs, it will likely take 5 to 10 minutes to download and search through all results. If run
regularly (see "Automatic Scheduling" below), each run will take less than a minute. The program can always run in the background.

# Plug-and-Play Setup
## MacOS
Download `MacExecutable.zip` from this repository and unzip it. A `testvault-alerts` folder
will appear containing the `testvault-alert-sender` executable.

1. Double click `testvault-alert-sender` to run. On first launch a window will ask for
   your SMTP credentials, TestVault credentials and the clients list URL. The values are saved
   to `config.json` in your user configuration directory.
2. A file picker will then ask where downloaded PDFs should be saved. The location is remembered for
   future runs. Run the executable from the command line with the `--reset-config` flag to choose a new folder.

# Configuration

On first launch a small window requests your SMTP email, SMTP password, TestVault email,
TestVault password and the clients list URL. These values are saved to `config.json` in a
platform‑appropriate configuration directory. Delete or edit this file if you need to update
the credentials later.


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
results and then emails your SMTP address with a summary of any clients whose tests were
positive for one or more drugs.

# Automatic Scheduling
I suggest using launchd (on MacOS) or Task Scheduler (on Windows) to run alertSender.py at scheduled times or intervals.
Allowing alertSender/testvault-alert-sender to run automatically once or twice a day results in an email notification
whenever new results are uploaded without any user interaction. Emails also list the chosen download directory and the 
clients with positive results, expediting the process of checking for concerning results
