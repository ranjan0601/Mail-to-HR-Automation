import csv
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv # Load environment variables from .env file if it exists
import re
load_dotenv()

# -----------------------------
# Basic configuration
# -----------------------------

# CSV file should contain at least one column named: email
# Optional columns supported by this script: name, company
CSV_FILE = "hr_contacts.csv"

# Path to your CV/resume file.
CV_FILE = "amit_ranjan_CV.pdf"

# Change this to False only after checking your email draft/output.
DRY_RUN = False

# SMTP settings for Gmail.
# If you use Gmail, create an App Password and use it as SMTP_PASSWORD.
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Keep sensitive values in environment variables instead of writing them here.
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def is_valid_email(email):
    """
    Basic email validation to skip clearly invalid addresses.
    """
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    if not re.match(pattern, email):
        return False

    domain = email.split("@", 1)[1]

    # Domain names cannot contain underscores.
    if "_" in domain:
        return False

    return True


def read_hr_contacts(csv_file):
    """
    Read HR contact details from a CSV file.

    Expected CSV example:
    email,name,company
    hr@example.com,Anita Sharma,ABC Technologies
    careers@example.com,,XYZ Pvt Ltd
    """
    contacts = []

    with open(csv_file, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            email = row.get("email", "").strip()

            # Skip rows where email is missing.
            if not email:
                continue

            contacts.append({
                "email": email,
                "name": row.get("name", "").strip(),
                "company": row.get("company", "").strip(),
            })

    return contacts


def create_email_message(receiver_email, receiver_name, company_name, cv_file):
    """
    Create an email message with subject, body, and CV attachment.
    """
    subject = "Application for Python Developer Opportunity"

    greeting_name = receiver_name if receiver_name else "HR Team"
    company_text = f" at {company_name}" if company_name else ""

    body = f"""Dear {greeting_name},

I hope you are doing well.

I am writing to express my interest in MIS Analyst|Data Manager|Automation Expert| Python Developer opportunities{company_text}. I have attached my CV for your review.

I would be grateful if you could consider my profile for any suitable openings. Please let me know if any additional details are required.

Thank you for your time and consideration.

Best regards,
Amit Ranjan
+91 - 8097221766
Linkedin (https://www.linkedin.com/in/amit-ranjan-aa986b50) / Github (https://github.com/ranjan0601)
"""

    message = EmailMessage()
    message["From"] = SENDER_EMAIL
    message["To"] = receiver_email
    message["Subject"] = subject
    message.set_content(body)

    attach_cv(message, cv_file)
    return message


def attach_cv(message, cv_file):
    """
    Attach the CV file to the email message.
    """
    cv_path = Path(cv_file)

    if not cv_path.exists():
        raise FileNotFoundError(f"CV file not found: {cv_file}")

    with open(cv_path, "rb") as file:
        file_data = file.read()
        file_name = cv_path.name

    message.add_attachment(
        file_data,
        maintype="application",
        subtype="octet-stream",
        filename=file_name,
    )


def send_email(message):
    """
    Send one email using SMTP.
    """
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        server.send_message(message)


def validate_settings():
    """
    Check required files and email credentials before sending.
    """
    if not Path(CSV_FILE).exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")

    if not Path(CV_FILE).exists():
        raise FileNotFoundError(f"CV file not found: {CV_FILE}")

    if not SENDER_EMAIL:
        raise ValueError("Please set the SENDER_EMAIL environment variable.")

    if not DRY_RUN and not SMTP_PASSWORD:
        raise ValueError("Please set the SMTP_PASSWORD environment variable.")


def send_emails_to_hr_contacts():
    """
    Loop through each HR email from the CSV file and send the email.
    Invalid/refused emails are skipped and the script continues.
    """
    validate_settings()
    contacts = read_hr_contacts(CSV_FILE)

    if not contacts:
        print("No valid HR contacts found in the CSV file.")
        return

    for contact in contacts:
        receiver_email = contact["email"]

        if not is_valid_email(receiver_email):
            print(f"Skipped invalid email address: {receiver_email}")
            continue

        message = create_email_message(
            receiver_email=receiver_email,
            receiver_name=contact["name"],
            company_name=contact["company"],
            cv_file=CV_FILE,
        )

        if DRY_RUN:
            print("----------------------------------------")
            print(f"DRY RUN: Email prepared for {receiver_email}")
            print(f"Subject: {message['Subject']}")
            print("Email was not sent because DRY_RUN is True.")
            continue

        try:
            send_email(message)
            print(f"Email sent successfully to {receiver_email}")

        except smtplib.SMTPRecipientsRefused as error:
            print(f"Skipped refused recipient: {receiver_email} | {error}")
            continue

        except smtplib.SMTPException as error:
            print(f"Skipped due to SMTP error: {receiver_email} | {error}")
            continue

        except Exception as error:
            print(f"Skipped due to unexpected error: {receiver_email} | {error}")
            continue


if __name__ == "__main__":
    send_emails_to_hr_contacts()
