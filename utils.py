import logging
import logging.config
import os
import smtplib
import time
import warnings
from email.message import EmailMessage

import yaml
from dotenv import load_dotenv
from infisical_client import ClientSettings, InfisicalClient, ListSecretsOptions


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


def load_infisical_env_variables(
    client_id: str | None = None,
    client_secret: str | None = None,
    environment: str = "dev",
    project_id: str | None = None,
) -> None:
    """Helper function to load env. variables from Infisical"""
    if client_id is None:
        client_id = os.getenv("INFISICAL_MACHINE_CLIENT_ID")
    if client_secret is None:
        client_secret = os.getenv("INFISICAL_MACHINE_CLIENT_SECRET")
    if project_id is None:
        project_id = os.getenv("PROJECT_ID")

    load_dotenv()
    
    client = InfisicalClient(
        ClientSettings(
            client_id=client_id,
            client_secret=client_secret,
        )
    )
    client.listSecrets(
        options=ListSecretsOptions(
            environment=environment,
            project_id=project_id,
            attach_to_process_env=True,
        ),
    )
