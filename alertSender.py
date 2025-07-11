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
import os
import smtplib
import argparse
import logging
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from config import (
    get_appdata_path,
    get_config_value,
    set_config_value, CONFIG_PATH,
)

import TestVaultScraper

# set up logging format
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

def send_email(smtp_server, port, username, password, recipient, subject, body):
    """
    Sends an email with the specified arguments
    """
    msg = EmailMessage()
    msg["From"] = username
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)
    
    with smtplib.SMTP_SSL(smtp_server, port) as smtp:
        smtp.login(username, password)
        smtp.send_message(msg)
        
def results_string(results):
    """
    Formats results (set of Tests) into a list of 'client on testdate'
    """
    results_str = ""
    for result in results:
        results_str += f"{result.client} on {result.collection_date}\n"
    return results_str

def get_download_dir():
    """
    Returns the path of the previously saved download directory, or prompts the user to pick one and saves it
    :return: Path, home/Downloads by default
    """
    saved = get_config_value("download_dir")
    if saved and Path(saved).exists():
        return saved
    chosen = prompt_for_download_dir()
    if chosen:
        set_config_value("download_dir", chosen)
        return chosen
    else:
        print("No folder selected. Using default folder.")
        return Path.home() / "Downloads"

def prompt_for_download_dir():
    """
    Prompts the user to select a download directory and returns it
    :return: the selected directory
    """
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title="TestVault Alerts: Choose Download Folder",
                        message="Please choose the folder where UA results should be saved. This selection will be remembered"
                                " for future use.")
    root.title("TestVault Alerts")
    folder = filedialog.askdirectory(title="Choose folder for UA results")
    root.destroy()
    return folder or None

#TODO add optional username field in popup
def prompt_for_credentials():
    """Show a Tkinter form asking for required credentials."""
    root = tk.Tk()
    root.title("TestVault Alerts Setup")
    fields = [
        ("SMTP Email", "smtp_user"),
        ("SMTP Password", "smtp_pass"),
        ("TestVault Email", "testvault_user"),
        ("TestVault Password", "testvault_pass"),
        ("Clients List URL", "clients_list_url"),
    ]
    entries = {}
    for i, (label, key) in enumerate(fields):
        tk.Label(root, text=label).grid(row=i, column=0, padx=5, pady=2, sticky="e")
        show = "*" if "Password" in label else None
        entry = tk.Entry(root, width=40, show=show)
        entry.grid(row=i, column=1, padx=5, pady=2)
        entries[key] = entry

    def submit():
        for k, e in entries.items():
            set_config_value(k, e.get().strip())
        root.destroy()

    tk.Button(root, text="Save", command=submit).grid(row=len(fields), column=0, columnspan=2, pady=10)
    root.mainloop()


def get_credentials():
    keys = [
        "smtp_user",
        "smtp_pass",
        "testvault_user",
        "testvault_pass",
        "clients_list_url",
    ]
    if not all(get_config_value(k) for k in keys):
        prompt_for_credentials()
    return {k: get_config_value(k) for k in keys}

        
def main():
    # constants
    TODAY_FORMATTED = datetime.today().strftime("%Y-%m-%d")

    # set up and retrieve command line arguments
    parser = argparse.ArgumentParser(description="Scan UA PDFs and e-mail alerts")
    parser.add_argument("--reset-config", action="store_true", help="Reset saved download directory")
    args = parser.parse_args()

    if args.reset_config:
        CONFIG_PATH.unlink()

    # setup folders
    download_dir = get_download_dir()
    results_dir = f"{download_dir}/{TODAY_FORMATTED}"
    
    # ensure credentials exist and download new results
    creds = get_credentials()
    new_results = TestVaultScraper.download_results(download_dir, get_appdata_path())

    if new_results:
        smtp_server = "smtp.gmail.com"
        port = 465
        username = creds["smtp_user"]
        if "@" not in username: #TODO allow use without email
            raise ValueError("Sender e-mail is not a valid e-mail address")
        password = creds["smtp_pass"]
        send_to = username
        subject = "New UA Results Alert"
    
        # 1) find any positives
        positives = set()
        body = (
        f"Found {len(new_results)} new results.\n"
        + f"New results for:\n{results_string(new_results)}\n"
        )
        
        # check for PDFs with positive results
        for result in new_results:
            if result.is_positive():
                positives.add(result)

        if positives:
            subject = "New UA Results Alert - ⚠️ Positive UA"
            body += (
                "The following clients have POSITIVE UA results:\n"
                + f"{results_string(positives)}\n"
                + f"\nCheck {results_dir} for details."
            )
        else:
            subject = "New UA Results Alert - All Negative"
            body += (
                "All results are negative."
                + f"\n\nCheck {results_dir} for details."
            )

        send_email(smtp_server, port, username, password, send_to, subject, body)
        print(f"Sent email to {send_to} reporting {len(new_results)} new results\n")
    else:
        print(f"{len(new_results)} new results were found, no email sent\n")
        
if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("alertSender.py terminated with an error")
        sys.exit(1)
        
