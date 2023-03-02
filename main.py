import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import csv
import logging
import threading

# Email subject
SUBJECT = "Judul Email"

# Static data for template
static_data = {
    's_example': 'example'
}

 # Load environment variables from .env file
load_dotenv()

# SMTP server details
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Email details
FROM_EMAIL = os.getenv('FROM_EMAIL')

# File
SENT_EMAIL_FILE = os.getenv('SENT_EMAIL_FILE')
RECIPIENTS_FILE = os.getenv('RECIPIENTS_FILE')
TEMPLATE_FILE = os.getenv('TEMPLATE_FILE')
LOG_FILE = os.getenv('LOG_FILE')

def main():
    # Initialize
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s %(message)s")
    lock = threading.Lock()

    global users_data, sent_emails
    users_data = {}
    sent_emails = []

    # Read recipients file
    with open(RECIPIENTS_FILE, "r") as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            users_data[row['email']] = row

    # Read sent emails file
    with open(SENT_EMAIL_FILE, "r") as file:
        sent_emails = file.read().splitlines()

    # Read HTML template from file
    with open(TEMPLATE_FILE, 'r') as file:
        html_template = file.read()

    # Replace static data with actual values
    for it in static_data:
        html_template = html_template.replace('{'+it+'}', static_data[it])

    def send_email(to_email):
        # Check if email has already been sent
        if(to_email in sent_emails):
            logging.info(f'Email to {to_email} has already been sent!')
            return

        # Replace template data with actual values
        for it in users_data[to_email]:
            html = html_template.replace('{'+it+'}', users_data[to_email][it])

        # Create message container
        message = MIMEMultipart('alternative')
        message['From'] = FROM_EMAIL
        message['To'] = to_email
        message['Subject'] = SUBJECT

        # Attach HTML message
        message.attach(MIMEText(html, 'html'))

        # Connect to SMTP server and send email
        smtp_server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        smtp_server.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp_server.sendmail(FROM_EMAIL, to_email, message.as_string())
        smtp_server.quit()

        # Mark email as sent
        with lock:
            sent_emails.append(to_email)
            with open(SENT_EMAIL_FILE, "a") as file:
                file.write(to_email + "\n")

        logging.info(f'Email sent to {to_email} successfully!')


    # Create a thread pool executor to run the send_email function for each recipient concurrently
    with ThreadPoolExecutor() as executor:
        executor.map(send_email, users_data)

    logging.info('All emails sent!')
    print('All emails sent!')

if __name__ == '__main__':
    main()
