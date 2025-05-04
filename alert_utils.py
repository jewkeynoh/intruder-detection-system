# -*- coding: utf-8 -*-
"""
Utility functions for sending notifications (Email, SMS, App).
Loads credentials securely using python-dotenv from a .env file.
Requires configuration settings from config.py.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import logging
import requests
from twilio.rest import Client as TwilioClient
from pathlib import Path
import os
from dotenv import load_dotenv
import datetime
import threading

try:
    import config
except ImportError:
    print("[CRITICAL ERROR] config.py not found. Cannot run alert_utils.")
    exit(1)

logger = logging.getLogger(__name__)

# --- Load Credentials Securely ---
dotenv_path = config.PROJECT_ROOT / ".env"
if dotenv_path.is_file():
    # Logging might not be fully configured here yet if called early
    # print(f"Loading environment variables from: {dotenv_path}") # Use print if logger fails
    load_dotenv(dotenv_path=dotenv_path)
# else:
    # print(f".env file not found at {dotenv_path}. Credentials might be missing.") # Use print

GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")

# --- Email Alert ---
def send_email_alert(subject, body, image_path=None):

    if not config.ENABLE_EMAIL_ALERT:
        logger.debug("Email alert is disabled in config.")
        return
    # ... (rest of the checks and message preparation as before) ...
    if not all([config.EMAIL_SENDER, GMAIL_APP_PASSWORD, config.EMAIL_RECEIVER]):
        logger.error("Email configuration incomplete (sender, password, receiver). Cannot send email.")
        return

    logger.info(f"Preparing email alert for {config.EMAIL_RECEIVER}...")
    message = MIMEMultipart("related")
    message["Subject"] = subject
    message["From"] = config.EMAIL_SENDER
    message["To"] = config.EMAIL_RECEIVER
    message.preamble = 'This is a multi-part message in MIME format.'
    message_alternative = MIMEMultipart('alternative')
    message.attach(message_alternative)
    message_text = MIMEText(body, 'plain')
    message_alternative.attach(message_text)

    if image_path and Path(image_path).is_file():
        try:
            with open(image_path, 'rb') as img_file:
                mime_image = MIMEImage(img_file.read(), _subtype='jpeg')
                mime_image.add_header('Content-Disposition', f'attachment; filename="{Path(image_path).name}"')
                message.attach(mime_image)
                logger.info(f"Attached image {Path(image_path).name} to email.")
        except IOError as e:
            logger.error(f"Could not read or attach image file {image_path}: {e}")
    else:
        logger.warning(f"Image path invalid or not provided ({image_path}), sending email without image.")

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT, context=context) as server:
            server.login(config.EMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(config.EMAIL_SENDER, config.EMAIL_RECEIVER, message.as_string())
            # *** ADDED LOGGING CONFIRMATION ***
            logger.info(f"Email alert successfully sent to {config.EMAIL_RECEIVER}.")
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication Error: Check sender email and App Password in .env file.")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

# --- SMS Alert (Twilio Example) ---
def send_sms_alert(message_body):
    if not config.ENABLE_SMS_ALERT:
        logger.debug("SMS alert is disabled in config.")
        return
    # ... (rest of the checks as before) ...
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, config.TWILIO_PHONE_NUMBER, config.SMS_RECIPIENT_NUMBER]):
        logger.error("Twilio SMS configuration incomplete in config or .env. Cannot send SMS.")
        return

    logger.info(f"Sending SMS alert to {config.SMS_RECIPIENT_NUMBER}...")
    try:
        client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message_body,
            from_=config.TWILIO_PHONE_NUMBER,
            to=config.SMS_RECIPIENT_NUMBER
        )
        # *** ADDED LOGGING CONFIRMATION ***
        # Note: Success here means Twilio accepted it, not necessarily delivered.
        logger.info(f"SMS alert successfully sent via Twilio to {config.SMS_RECIPIENT_NUMBER}. SID: {message.sid}")
    except Exception as e:
        logger.error(f"Failed to send SMS via Twilio: {e}")

# --- App Notification (Pushover Example) ---
def send_pushover_notification(title, message, image_path=None):
    if not config.ENABLE_PUSHOVER_ALERT:
        logger.debug("Pushover alert is disabled in config.")
        return
    # ... (rest of the checks and file handling as before) ...
    if not all([PUSHOVER_API_TOKEN, PUSHOVER_USER_KEY]):
        logger.error("Pushover configuration incomplete (API token, User key in .env). Cannot send notification.")
        return

    logger.info(f"Sending Pushover notification...") # User key masked later
    payload = { "token": PUSHOVER_API_TOKEN, "user": PUSHOVER_USER_KEY, "title": title, "message": message, "priority": 1 }
    files = None
    opened_file = None

    if image_path and Path(image_path).is_file() and config.PUSHOVER_SEND_IMAGE:
         try:
             opened_file = open(image_path, "rb")
             files = { "attachment": (Path(image_path).name, opened_file, "image/jpeg") }
             logger.info("Attaching image to Pushover notification.")
         except IOError as e:
             logger.error(f"Could not open image {image_path} for Pushover: {e}")
             if opened_file: opened_file.close()
             files, opened_file = None, None

    try:
        response = requests.post("https://api.pushover.net/1/messages.json", data=payload, files=files, timeout=30)
        response.raise_for_status()
        # *** ADDED LOGGING CONFIRMATION ***
        # Pushover response includes status=1 on success
        if response.json().get('status') == 1:
             logger.info(f"Pushover notification sent successfully (User: {PUSHOVER_USER_KEY[:5]}...). Request ID: {response.json().get('request')}")
        else:
             logger.warning(f"Pushover request succeeded but status was not 1: {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Pushover notification: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred sending Pushover notification: {e}")
    finally:
        if opened_file: opened_file.close()

# --- App Notification (ntfy.sh Example) ---
def send_ntfy_notification(title, message, image_path=None):
    if not config.ENABLE_NTFY_ALERT:
        logger.debug("ntfy alert is disabled in config.")
        return
    # ... (rest of the checks and data preparation as before) ...
    if not config.NTFY_TOPIC:
         logger.error("ntfy.sh topic not configured in config.py.")
         return

    ntfy_url = f"{config.NTFY_SERVER.rstrip('/')}/{config.NTFY_TOPIC}"
    logger.info(f"Sending ntfy notification to topic {config.NTFY_TOPIC}...")
    headers = {"Title": title.encode('utf-8')}
    data = message.encode('utf-8')
    opened_file_for_ntfy = None # Track if we need to close a file handle

    if image_path and Path(image_path).is_file() and config.NTFY_SEND_IMAGE:
         headers['Filename'] = Path(image_path).name.encode('utf-8')
         try:
              # Read directly into data, no need to keep file open usually
              with open(image_path, 'rb') as img_file:
                  data = img_file.read()
              logger.info("Sending image data via ntfy.")
         except IOError as e:
              logger.error(f"Could not read image {image_path} for ntfy: {e}")
              data = message.encode('utf-8')
              headers.pop('Filename', None)
    else:
        logger.debug("Sending text-only ntfy notification.")

    try:
        req_method = requests.put if 'Filename' in headers else requests.post
        response = req_method(ntfy_url, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        # *** ADDED LOGGING CONFIRMATION ***
        # ntfy returns JSON with topic, message, title etc on success
        logger.info(f"ntfy.sh notification sent successfully to topic {config.NTFY_TOPIC}.")
        # logger.debug(f"ntfy response: {response.text}") # Optional: log full response
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send ntfy.sh notification to {ntfy_url}: {e}")
        # You might want to log response.text here too for debugging errors
        # try: logger.error(f"ntfy error response: {e.response.text}")
        # except: pass
    except Exception as e:
        logger.error(f"An unexpected error occurred sending ntfy.sh notification: {e}")
    # No file handle to close here as we used 'with open' or didn't open one

# --- Central Alert Trigger ---
def trigger_notifications(subject, text_body, sms_body, image_path=None):
    """Calls enabled notification functions, potentially in threads."""
    logger.info(f"Notification trigger called. Image: {image_path}")

    threads = []
    # Start a thread for each enabled alert type
    if config.ENABLE_EMAIL_ALERT:
        thread = threading.Thread(target=send_email_alert, args=(subject, text_body, image_path), daemon=True)
        threads.append(thread)
        thread.start()
    if config.ENABLE_SMS_ALERT:
         thread = threading.Thread(target=send_sms_alert, args=(sms_body,), daemon=True)
         threads.append(thread)
         thread.start()
    if config.ENABLE_PUSHOVER_ALERT:
        thread = threading.Thread(target=send_pushover_notification, args=(subject, text_body, image_path), daemon=True)
        threads.append(thread)
        thread.start()
    if config.ENABLE_NTFY_ALERT:
        thread = threading.Thread(target=send_ntfy_notification, args=(subject, text_body, image_path), daemon=True)
        threads.append(thread)
        thread.start()

    # Wait for all alert threads to complete before potentially deleting image
    for i, thread in enumerate(threads):
        thread.join(timeout=60) # Add a timeout to prevent waiting forever
        if thread.is_alive():
            logger.warning(f"Alert thread {i} did not finish within timeout.")

    logger.info("All triggered notification threads completed or timed out.")

    # --- CONDITIONAL IMAGE DELETION ---
    if config.DELETE_INTRUDER_IMAGE_AFTER_ALERT:
        if image_path and Path(image_path).is_file():
            try:
                os.remove(image_path)
                logger.info(f"Removed intruder image as configured: {image_path}")
            except OSError as e:
                logger.error(f"Error removing intruder image {image_path}: {e}")
        else:
             logger.warning(f"Configured to delete image, but path was invalid or None: {image_path}")
    else:
         if image_path: # Log even if not deleting
              logger.info(f"Intruder image kept as configured: {image_path}")