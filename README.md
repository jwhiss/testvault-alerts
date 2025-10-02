# TestVault Alerts

This repository gets drug test results from thetestvault.com and can alert via email when new results are available, 
including a list of clients for whom one or more individual drugs were present. 

The first time this program runs, it will likely take 5 to 10 minutes to download and search through all results. If run
regularly (see "Automatic Scheduling" below), each run will usually take less than a minute. The program can always run 
in the background.

# Plug-and-Play Setup
## MacOS
Download `MacExecutable.zip` from this repository and unzip it by double-clicking on the file. A `TestVault Alert Sender` 
folder will appear containing the `testvault-alerts` executable, a `README.md` file containing these instructions, an 
`_internal` folder which must stay in the same folder as the executable, and the license for modifying and distributing 
this program.

## Windows
Download `WindowsExecutable.zip` from this repository and unzip it by right-clicking on it and selecting "Extract All". 
A `TestVault Alert Sender` folder will appear containing the `testvault-alerts.exe` executable, a `README.md` file 
containing these instructions, an `_internal` folder which must stay in the same folder as the executable, and the 
license for modifying and distributing this program.

## Running testvault-alerts
1. Double click `testvault-alerts` executable to run.
2. A file picker will then ask where downloaded PDFs should be saved. The location is remembered for
   future runs. Run the executable from the command line with the `--reset-config` flag to run with setup prompts again.
3. Another window will ask for your TestVault credentials, SMTP (email) credentials, and the clients list URL (see 
"Configuration"). Select "Remember these settings and don't ask again" to save the credentials to a locally-stored 
configuration file. These credentials never leave your device, except when sent to TestVault or SMTP servers.

# Configuration

On first launch a small window requests your SMTP email, SMTP password, TestVault email, TestVault password, the 
clients list URL, and an optional keyword.

The three TestVault fields are required, while the two SMTP (email credential) fields are optional but highly recommended 
as they enable the email alert functionality. Without SMTP credentials, PDFs of new results will still be downloaded but 
program output will appear only in a Terminal window, rather than being sent to you through email.

The "Clients List URL" field is required to access the TestVault website and retrieve results. To find this URL:
1. Log in to TestVault and click on the "Groups" tab near the top of the page.
2. Click on your company or house name
3. Copy the URL of the current page and paste it into the configuration popup window

The optional "Keyword" field allows you to set a custom keyword for the program to use when checking PDF results for 
positive tests. By default, the presence of "above", "reportable", or "Inconsistent Result" in a PDF will count that PDF 
as a positive result. To override the default keywords, type one keyword into the field. This keyword must be present only 
in PDFs with positive results. The keyword is case-sensitive. 

Credentials are saved to `config.json` in a platform‑appropriate application data directory, and remembered as long as 
"Remember these settings and don't ask again" is checked. To get this configuration window again, either don't check the 
box or run alertSender or testvault-alerts from the command line with `--reset-config`

## Email account access
To send test results via email, the program requires your email (SMTP) access credentials. If you have two-factor authentication
enabled for your account, your regular password will not be accepted. Instead, create a new "app password" for use 
with this program. For gmail, you can create an app password here: https://myaccount.google.com/apppasswords. Once
you've created an app password, fill in the SMTP email and password fields in the configuration popup window with your
email address and the generated app password. 

# Manual Setup

## System Requirements

Before running or building the project ensure these system packages are installed:

- **Python** – Necessary for compiling and running the program. Tkinter must be included with your python distribution.
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
positive for one or more drugs. By default, the `is_positive()` function in TestVaultScraper.py checks for "reportable" or 
"above" in the given PDF to determine if a test is positive. The function accepts a set of keywords as an argument, so 
if your testing provider uses different phrasing to indicate a positive result you can override the default argument. 

# Automatic Scheduling
I suggest using launchd (on macOS) or Task Scheduler (on Windows) to run alertSender.py at scheduled times or intervals.
Allowing alertSender/testvault-alerts to run automatically once or twice a day results in an email notification
whenever new results are uploaded without any user interaction. Emails also list the chosen download directory and the 
clients with positive results, expediting the process of checking for concerning results
