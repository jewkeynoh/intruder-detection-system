# -*- coding: utf-8 -*-
"""
Configuration settings for the Intruder Detection System.
"""

import os
from pathlib import Path

# --- Project Root ---
PROJECT_ROOT = Path(__file__).parent.resolve()

# --- Directory Paths ---
KNOWN_FACES_DIR = PROJECT_ROOT / "known_faces"
OUTPUT_DIR = PROJECT_ROOT  # For encodings file
LOG_DIR = PROJECT_ROOT / "logs"
INTRUDER_IMAGE_DIR = PROJECT_ROOT / "intruder_images" # For saving intruder pics

# --- File Paths ---
ENCODINGS_FILE_NAME = "known_face_encodings.pkl"
ENCODINGS_PATH = OUTPUT_DIR / ENCODINGS_FILE_NAME
LOG_FILE_NAME = "intruder_alert.log"
LOG_FILE = LOG_DIR / LOG_FILE_NAME

# --- Face Recognition Model ---
DETECTION_MODEL = 'hog' # 'hog' (faster) or 'cnn' (accurate)
UPSAMPLE_TIMES = 1
NUM_JITTERS = 1

# --- Face Comparison ---
MATCH_TOLERANCE = 0.6 # Lower = stricter matching

# --- Real-time Detection Settings ---
FRAME_PROCESS_SCALE = 0.5 # Resize frame for speed (1.0 = no resize)
PROCESS_EVERY_N_FRAMES = 2 # Process every Nth frame

# --- Intruder Detection Logic ---
UNKNOWN_FRAMES_THRESHOLD = 3 # Trigger alert after N consecutive processed frames with Unknown (recommended 10)
ALERT_COOLDOWN_SECONDS = 300  # Min seconds between alerts (e.g., 300 = 5 minutes)

# --- Intruder Image Handling ---
DELETE_INTRUDER_IMAGE_AFTER_ALERT = False # Set to False to keep intruder images permanently

# --- Alert Service Configuration Flags (Set to True to enable) ---
ENABLE_EMAIL_ALERT = True
ENABLE_SMS_ALERT = False
ENABLE_PUSHOVER_ALERT = False
ENABLE_NTFY_ALERT = False # Example using ntfy.sh

# --- Email Alert Settings ---
# Required if ENABLE_EMAIL_ALERT = True
EMAIL_SENDER = "micodioquino17@gmail.com"
EMAIL_RECEIVER = "fingerstyler17@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465 # For SSL
# EMAIL_PASSWORD -> Load GMAIL_APP_PASSWORD from .env

# --- SMS Alert Settings (Twilio Example) ---
# Required if ENABLE_SMS_ALERT = True
TWILIO_PHONE_NUMBER = "+1_your_twilio_number"
SMS_RECIPIENT_NUMBER = "+countrycode_your_phone_number"
# TWILIO_ACCOUNT_SID -> Load from .env
# TWILIO_AUTH_TOKEN -> Load from .env

# --- App Notification Settings (Pushover Example) ---
# Required if ENABLE_PUSHOVER_ALERT = True
PUSHOVER_SEND_IMAGE = True # Try to send image with notification
# PUSHOVER_API_TOKEN -> Load from .env
# PUSHOVER_USER_KEY -> Load from .env

# --- App Notification Settings (ntfy.sh Example) ---
# Required if ENABLE_NTFY_ALERT = True
NTFY_TOPIC = "your_secret_ntfy_topic_name" # Choose a hard-to-guess topic
NTFY_SERVER = "https://ntfy.sh" # Public server or your self-hosted one
NTFY_SEND_IMAGE = True

# --- Display Settings (OpenCV Window) ---
CV2_FONT_NAME = 'FONT_HERSHEY_DUPLEX'
FONT_SCALE = 0.6
FONT_THICKNESS = 1
BOX_COLOR_KNOWN = (0, 255, 0)      # Green
TEXT_COLOR_KNOWN = (255, 255, 255) # White
BOX_COLOR_UNKNOWN = (0, 0, 255)    # Red
TEXT_COLOR_UNKNOWN = (255, 255, 255)# White
FPS_POSITION = (5, 25)

# --- Logging Configuration ---
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s'

# --- Ensure directories exist ---
# (Keep the directory creation logic as before)
try:
    KNOWN_FACES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    INTRUDER_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
except OSError as e:
    print(f"[CRITICAL ERROR] Failed to create necessary directories: {e}")
    import sys
    sys.exit(1)