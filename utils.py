import os
import smtplib
from email.message import EmailMessage
import logging
import logging.config
import time
import warnings
import yaml


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


def setup_logger(
    logger_name: str, log_config_file: str, log_file: str = "file1.log"
) -> logging.Logger:
    if not log_config_file:
        raise ValueError("Please provide a log configuration file path.")
    
    with open(log_config_file, "r") as f:
        config = yaml.safe_load(f.read())

        # set the filename for the RotatingFileHandler
        config["handlers"]["file"]["filename"] = log_file

        # apply logging config to logging
        logging.config.dictConfig(config)

        if logger_name not in config["loggers"]:
            warnings.warn(
                "Beware! The logger name you provided does not match any logger defined in the logging config file. "
                f"({list(config['loggers'].keys())}). Using the root logger."
            )
            logger_name = "root"

        return logging.getLogger(logger_name)
