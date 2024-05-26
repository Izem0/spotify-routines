import logging
import logging.config
import os
import smtplib
import sys
import time
from email.message import EmailMessage


def send_email(
    sender="izem.mangione@gmail.com",
    receipient="izem.mangione@gmail.com",
    subject="",
    body="",
    html=None,
):
    """Send an email using smtp library. Optionnaly, provide html content to format your message using html."""

    msg = EmailMessage()

    # generic email headers
    msg["From"] = sender
    msg["To"] = receipient
    msg["Subject"] = subject

    # set the body of the mail
    msg.set_content(body)

    if html:
        msg.add_alternative(html, subtype="html")

    # send it using smtplib
    email_address = os.getenv("GMAIL_ADDRESS")
    email_password = os.getenv("GMAIL_PASSWORD")
    with smtplib.SMTP_SSL("smtp.gmail.com", 0) as smtp:
        smtp.login(email_address, email_password)
        smtp.send_message(msg)


def setup_logger(
    name: str = __name__,
    datefmt: str = "%Y-%m-%d %H:%M:%S%z",
    handlers: list = None,
    level="INFO",
):
    """Generate a logger"""
    if not handlers:
        handlers = [logging.StreamHandler(sys.stdout)]  # print to console

    logging.basicConfig(
        format="%(name)s | [%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        datefmt=datefmt,
        handlers=handlers,
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


def timer(logger=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            t1 = time.perf_counter()
            result = func(*args, **kwargs)
            t2 = time.perf_counter()
            execution_time = t2 - t1
            if logger:
                logger.info(
                    f"Execution time of '{func.__name__}': {execution_time:.2f} seconds"
                )
            else:
                print(
                    f"Execution time of '{func.__name__}': {execution_time:.2f} seconds."
                )
            return result

        return wrapper

    return decorator
