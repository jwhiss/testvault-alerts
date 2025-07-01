#!/Users/joel/eclipse-workspace/UAScraper/UAvenv/bin/python
import os
import smtplib
import argparse
from email.message import EmailMessage
from dotenv import load_dotenv # for SMTP username/password

import TestVaultScraper           

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
        
def main():
    # set up and retrieve command line arguments
    parser = argparse.ArgumentParser(description="Scan UA PDFs and e-mail alerts")
    parser.add_argument("--download-dir", default="/Users/joel/Documents/SSL/LabUAs",
                        help="Folder where results directory should appear")
    args = parser.parse_args()
    
    load_dotenv()
    
    # email info from .env
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
    
    # download new results and store directories
    test_dirs, new_results = TestVaultScraper.download_results(args.download_dir)
    
    # 1) find any positives
    positives = set()
    if len(new_results) == 0:
        body = "Found 0 new results.\n"
    else:
        body = (
        f"Found {len(new_results)} new results.\n"
        + f"New results for:\n{results_string(new_results)}\n"
        )
        
        # check for PDFs with positive results
        for result in new_results:
            if result.is_positive():
                positives.add(result)
        
        # send email
        if positives:
            subject = "New UA Results Alert - ⚠️ Positive UA"
            body += (
                "The following clients have POSITIVE UA results:\n"
                + f"{results_string(positives)}\n"
                + f"\nCheck {test_dirs} for details."
            )
        else:
            subject = "New UA Results Alert - All Negative"
            body += (
                "All results are negative."
                + f"\n\nCheck {test_dirs} for details."
            )
            
    send_email(smtp_server, port, username, password, send_to, subject, body)
    print(f"Sent email to {send_to} reporting {len(new_results)} new results\n")
        
if __name__ == "__main__":
    main()
        
