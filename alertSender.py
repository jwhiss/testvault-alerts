"""
Created on May 14, 2025

@author: Joel Whissel
"""
import json
import os
import smtplib
import argparse
import logging
import sys
import platform
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from email.message import EmailMessage
from dotenv import load_dotenv # for SMTP username/password
from pathlib import Path

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
        return saved;
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
    folder = filedialog.askdirectory(title="Choose download directory for UA results")
    root.destroy()
    return folder or None

def get_config_value(key):
    """
    Returns the value with the given key from CONFIG_PATH, or None if the pair does not exist
    :param key: str, the key to look for
    """
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f).get(key)
        except Exception:
            pass
    return None

def set_config_value(key, value):
    """
    Sets the given key to the given value in CONFIG_PATH
    :param key: str, key to set in CONFIG_PATH
    :param value: str, value to be matched with the given key
    """
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump({key: value}, f)

def get_appdata_path():
    """
    Returns the path to the configuration file based on standards for the current platform
    :return:
    """
    system = platform.system()
    if system == "Windows":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif system == "Darwin":  # macOS
        base = Path.home() / "Library" / "Application Support"
    else:  # Linux and everything else
        base = Path.home() / ".config"

    return base / "testvault-alerts"

# set config file path
CONFIG_PATH = get_appdata_path() / "config.json"
        
def main():
    TODAY_FORMATTED = datetime.today().strftime("%Y-%m-%d")

    # set up and retrieve command line arguments
    parser = argparse.ArgumentParser(description="Scan UA PDFs and e-mail alerts")
    parser.add_argument("--reset-config", action="store_true", help="Reset saved download directory")
    args = parser.parse_args()

    # setup folders
    download_dir = get_download_dir()
    prior_tests_dir = get_appdata_path() / "priorTests.csv"
    results_dir = f"{download_dir}/{TODAY_FORMATTED}"
    
    # download new results and store directories
    new_results = TestVaultScraper.download_results(download_dir, prior_tests_dir)

    if new_results:
        # email info from .env
        load_dotenv()
        smtp_server = "smtp.gmail.com"
        port = 465
        username = os.getenv("SMTP_USER")
        if "@" not in username:
            raise ValueError("Sender e-mail is not a valid e-mail address - "
                             "check SMTP_USER field in environment file")
        password = os.getenv("SMTP_PASS")
        send_to = os.getenv("SEND_TO", username)
        if "@" not in send_to:
            raise ValueError("Receiver e-mail is not a valid e-mail address - "
                             "check SEND_TO field in environment file")
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
        
