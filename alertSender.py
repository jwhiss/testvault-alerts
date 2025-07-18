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
    set_config_value, CONFIG_PATH, read_config,
)

import TestVaultScraper

# set up logging format
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

def create_email(new_results, positives, unreadables, results_dir):
    body = (f"Found {len(new_results)} new results.\n"
            + f"New results for:\n{results_string(new_results)}\n")

    if positives:
        subject = "New UA Results Alert - ⚠️ Positive UA"
        body += (
                "The following clients have POSITIVE UA results:\n"
                + f"{results_string(positives)}\n"
        )
    if unreadables:
        if not positives: subject = "New UA Results Alert - Unreadable results"
        body += (
                "The following clients have UNREADABLE UA results:\n"
                + f"{results_string(unreadables)}\n"
        )
    if not (positives or unreadables):
        subject = "New UA Results Alert - All Negative"
        body += (
                "All results are negative.\n"
        )
    body += f"\nCheck {results_dir} for details."
    return subject, body

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
                        message="Please choose the folder where UA results should be saved. "
                                "This selection will be remembered for future sessions.")
    root.title("TestVault Alerts")
    folder = filedialog.askdirectory(title="Choose folder for UA results")
    root.destroy()
    return folder or None

#TODO add optional username field in popup
def prompt_for_credentials():
    """Show a Tkinter form asking for required credentials."""
    root = tk.Tk()
    root.title("TestVault Alerts Setup")
    subtitle = tk.Label(root, text="Credentials are stored on your device and only sent to "
                                   "TestVault and SMTP servers.\nFields marked with '*' are required. "
                                   "SMTP (email login) fields are necessary for alert functionality.")
    subtitle.grid(row=0, columnspan=2, padx=5, pady=2, sticky="e")

    # credential fields
    fields = [
        ("TestVault Email *", "testvault_user"),
        ("TestVault Password *", "testvault_pass"),
        ("Clients List URL *", "clients_list_url"),
        ("SMTP Email", "smtp_user"),
        ("SMTP Password", "smtp_pass"),
    ]
    entries = {}
    for i, (label, key) in enumerate(fields):
        tk.Label(root, text=label).grid(row=i+2, column=0, padx=5, pady=2, sticky="e")
        show = "*" if "Password" in label else None
        entry = tk.Entry(root, width=40, show=show)
        entry.grid(row=i+2, column=1, padx=5, pady=2)
        entries[key] = entry

    # Remember settings checkbox
    remember_var = tk.BooleanVar(value=True)
    remember_check = tk.Checkbutton(
        root, text="Remember these settings and don't ask again", variable=remember_var)
    remember_check.grid(row=len(entries)+2, columnspan=2, pady=(10, 0))
    entries["remember"] = remember_var

    def submit():
        for k, e in entries.items():
            set_config_value(k, e.get())
        root.destroy()

    tk.Button(root, text="Save", command=submit).grid(row=len(entries)+2, column=0, columnspan=2, pady=10)
    root.mainloop()


def get_credentials():
    required = [
        "testvault_user",
        "testvault_pass",
        "clients_list_url",
    ]
    if not all(get_config_value(k) for k in required):
        prompt_for_credentials()
    return read_config()

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
        # check for PDFs with positive results
        positives = set()
        unreadables = set()
        for result in new_results:
            is_positive = result.is_positive()
            if is_positive:
                positives.add(result)
            elif is_positive is None:
                unreadables.add(result)


        if creds.get("smtp_user") and creds.get("smtp_pass"):
            smtp_server = "smtp.gmail.com"
            port = 465
            username = creds.get("smtp_user")
            if "@" not in username:
                raise ValueError("Sender e-mail is not a valid e-mail address")
            password = creds.get("smtp_pass")
            send_to = username
            subject, body = create_email(new_results, positives, unreadables, results_dir)

            send_email(smtp_server, port, username, password, send_to, subject, body)
            print(f"Sent email to {send_to} reporting {len(new_results)} new results\n")
        else:
            print("No SMTP credentials provided, no email sent\n")
    else:
        print(f"{len(new_results)} new results were found, no email sent\n")

    if not creds.get("remember"):
        to_forget = ["testvault_user", "testvault_pass", "clients_list_url", "smtp_user", "smtp_pass"]
        for k in to_forget:
            set_config_value(k, "")
        
if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("alertSender.py terminated with an error")
        sys.exit(1)
        
