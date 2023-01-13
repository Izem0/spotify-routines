import os
import smtplib
from email.message import EmailMessage


def send_email(sender="izem.mangione@gmail.com", receipient="izem.mangione@gmail.com", subject='', body='', html=None):
    """Send an email using smtp library. Optionnaly, provide html content to format your message using html."""

    msg = EmailMessage()
    
    # generic email headers
    msg["From"] = sender
    msg["To"] = receipient
    msg["Subject"] = subject

    # set the body of the mail
    msg.set_content(body)

    if html:
        msg.add_alternative(html, subtype='html')

    # send it using smtplib
    email_address = os.getenv("GMAIL_ADDRESS")
    email_password = os.getenv("GMAIL_PASSWORD")
    with smtplib.SMTP_SSL("smtp.gmail.com", 0) as smtp:
        smtp.login(email_address, email_password)
        smtp.send_message(msg)
