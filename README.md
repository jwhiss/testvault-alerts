# TestVault Alerts

This repository scrapes drug test results from TestVault and can alert via email when new results are available. It relies on Selenium, OCR utilities and other third‑party tools.

## System Requirements

Before running or building the project ensure these system packages are installed:

- **Tesseract OCR** – used to read scanned PDFs.
- **Poppler** – `pdf2image` requires Poppler to convert PDFs to images.
- **Google Chrome** and **ChromeDriver** – Selenium controls Chrome to download results.

Packages can usually be installed from your system package manager. For example, on macOS using Homebrew:

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

## Building Stand‑alone Executables

Use [PyInstaller](https://pyinstaller.org/) to build executables. First install dependencies from `requirements.txt` and PyInstaller itself:

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### macOS

Run PyInstaller with the `--onefile` option to bundle everything into a single executable:

```bash
pyinstaller --onefile alertSender.py
```

The output binary appears in the `dist/` folder.

### Windows

On Windows use the same command in a command prompt with your Python environment activated:

```cmd
pyinstaller --onefile alertSender.py
```

The resulting executable will be created in `dist\`.

After building, distribute the executable along with the `.env` file and ensure the system packages mentioned above are installed on the target machine.
