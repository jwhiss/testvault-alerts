# TestVault Alerts

This repository scrapes drug test results from thetestvault.com and can alert via email when new results are available, 
including a list of clients for whom one or more individual drugs were present. It relies on Selenium, OCR utilities and 
other third‑party tools.

The first time this program runs, it will likely take 5 to 10 minutes to download and search through all results. If run
regularly (see "Automatic Scheduling" below), each run will usually take less than a minute. The program can always run 
in the background.

# Plug-and-Play Setup
## MacOS
Download `MacExecutable.zip` from this repository and unzip it. A `TestVault Alert Sender` folder
will appear containing the `testvault-alerts` executable.

1. Double click `testvault-alerts` to run. 
2. A file picker will then ask where downloaded PDFs should be saved. The location is remembered for
   future runs. Run the executable from the command line with the `--reset-config` flag to run with setup prompts again. 
3. Another window will ask for your TestVault credentials, SMTP (email) credentials, and the clients list URL. These 
   values never leave your device, except when sent to TestVault or SMTP servers. 

## Windows
Plug-and-play setup is not yet available for Windows devices. Use the "Manual Setup" steps below.

# Configuration

On first launch a small window requests your SMTP email, SMTP password, TestVault email, TestVault password and the 
clients list URL. 

The three TestVault fields are required, while the two SMTP fields are optional but highly recommended as they enable 
the email alert functionality. Without SMTP credentials, PDFs of new results will still be downloaded but program output 
will appear only in a Terminal window, rather than being sent to you through email.

Credentials are saved to `config.json` in a platform‑appropriate application data directory, and remembered as long as 
"Remember these settings and don't ask again" is checked. To get this configuration window again, either don't check the 
box or run alertSender or testvault-alerts from the command line with `--reset-config`

## Email account access
To send test results via email, the program requires your email access credentials. If you have two-factor authentication
enabled for your account, your regular password will not be accepted. Instead, create a new "app password" for use 
with this program. For gmail, you can create an app password here: https://myaccount.google.com/apppasswords

# Manual Setup

## System Requirements

Before running or building the project ensure these system packages are installed:

- **Python** – Necessary for compiling and running the program. Tkinter must be included with your python distribution.
- **Tesseract OCR** – used to read scanned PDFs.
- **Poppler** – `pdf2image` requires Poppler to convert PDFs to images.
- **Google Chrome** and **ChromeDriver** – Selenium controls Chrome to download results.

Packages can usually be installed from your system package manager. For example, on macOS using Homebrew:
```bash
brew install tesseract poppler
brew install --cask google-chrome chromedriver
```

On Windows, download and install the Tesseract, Poppler and Chrome/ChromeDriver packages and ensure their executables 
are in your `PATH`.

Once you have downloaded this repository and installed python and the above packages, install the specific python 
packages needed for this program. Navigate to the directory containing the repository, then use pip:
```bash
pip install -r requirements.txt
```

## Running The Program
By design, alertSender.py should be run for full functionality.

If run individually, TestVaultScraper.py scrapes TestVault for new results and downloads any new results to your Downloads
folder.

alertSender.py remembers the download folder and credentials you use the first time it runs.
Use the `--reset-config` flag to choose a new folder. 

When alertSender.py is run it downloads new results, checks each PDF for positive
results and then emails your SMTP address with a summary of any clients whose tests were
positive for one or more drugs.

# Automatic Scheduling
I suggest using launchd (on macOS) or Task Scheduler (on Windows) to run alertSender.py at scheduled times or intervals.
Allowing alertSender/testvault-alerts to run automatically once or twice a day results in an email notification
whenever new results are uploaded without any user interaction. Emails also list the chosen download directory and the 
clients with positive results, expediting the process of checking for concerning results
