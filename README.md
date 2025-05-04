# Real-time Intruder Detection System with Alerts

**(README Context: Sunday, May 4, 2025, 4:19 PM PST - Calasiao, Philippines)**

## Overview

This project uses face recognition to identify known individuals versus unknown persons ("intruders") in a real-time webcam feed. When an unknown person is persistently detected, the system triggers configurable alerts via Email, SMS (Twilio), and/or App Notifications (Pushover, ntfy.sh), optionally including an image of the detected individual.

It builds upon basic face recognition using Python, OpenCV, `face_recognition` (dlib), and adds alerting capabilities and more robust project structure.

## Features

* **Known Face Encoding:** Learns faces from images in the `known_faces` directory.
* **Real-time Intruder Detection:** Monitors webcam feed, identifies known vs. unknown faces.
* **Persistent Unknown Detection:** Triggers alerts only when an unknown face is detected for a configurable number of consecutive frames.
* **Multi-Channel Alerts:** Sends notifications via:
    * Email (Gmail SMTP with image attachment)
    * SMS (Twilio API)
    * App Push Notifications (Pushover with image attachment, ntfy.sh with optional image data)
* **Configurable:** Uses `config.py` for paths, models, thresholds, cooldowns, and enabling/disabling alert channels.
* **Secure Credential Handling:** Uses `.env` file (via `python-dotenv`) to keep API keys and passwords out of the code (**IMPORTANT!**).
* **Logging:** Detailed logging to console and file (`logs/intruder_alert.log`).
* **Intruder Image Capture:** Saves a snapshot of the frame when an alert is triggered.
* **Modular Code:** Alert logic separated into `alert_utils.py`.

## Project Structure

```text
intruder_alert_system/
├── venv/                   # Python virtual environment (created by user)
├── known_faces/            # Root directory for known face images
│   ├── Person1_Name/       # Subdirectory for each known person
│   │   └── image1.jpg      # Image(s) of Person1
│   └── ...
├── logs/                   # Directory for log output (created automatically)
│   └── intruder_alert.log
├── intruder_images/        # Directory for saved intruder images (created automatically)
│   └── intruder_YYYYMMDD_HHMMSS.jpg
├── .gitignore              # Git ignore file
├── config.py               # Central configuration settings
├── alert_utils.py          # Functions for sending alerts
├── face_encoder.py         # Script to encode known faces
├── intruder_detector.py    # Main script for detection and triggering alerts
├── requirements.txt        # Python package dependencies
├── .env.example            # Example environment variables file
├── .env                    # Actual environment variables (**DO NOT COMMIT**)
└── README.md               # This documentation file
# Optional: known_face_encodings.pkl # Output of face_encoder.py
# Optional: LICENSE              # Add your chosen license file
```

Prerequisites
System-Level Dependencies: Install these first.

Python: 3.6+ recommended.
pip: Python package installer.
CMake: Required by dlib. Install and ensure it's added to system PATH. Verify with cmake --version in a new terminal. (cmake.org)
C++ Compiler: Required by dlib.
Windows: Visual Studio Build Tools (with "Desktop development with C++" workload).
macOS: Xcode Command Line Tools (xcode-select --install).
Linux: build-essential (sudo apt update && sudo apt install build-essential).
External Service Accounts (Optional - for alerts):

Email (Gmail): A Gmail account. You will likely need to generate an App Password if 2FA is enabled (link).
SMS (Twilio): A Twilio account (twilio.com). You'll need Account SID, Auth Token, and a Twilio Phone Number. (Note: Twilio costs money).
App Notification (Pushover): A Pushover account (pushover.net). You'll need an API Token and User Key. (Note: Small one-time fee).
App Notification (ntfy.sh): Optional. Use the public server (ntfy.sh) or self-host. Choose a unique topic name.
Setup
Clone/Download: Get the project files and cd into the intruder_alert_system directory.

Create Virtual Environment:

Bash

python -m venv venv
Activate Virtual Environment:

Bash

# Windows (cmd): .\venv\Scripts\activate.bat
# Windows (PS):  .\venv\Scripts\Activate.ps1
# Linux/macOS:   source venv/bin/activate
Install Python Dependencies:

Bash

# Ensure venv is active!
pip install -r requirements.txt
(This installs face_recognition, opencv-python, numpy, requests, twilio, python-dotenv)

Configure Credentials (CRITICAL SECURITY STEP):

Copy .env.example to .env:
Bash

# Linux/macOS
cp .env.example .env
# Windows
copy .env.example .env
Edit .env: Open the new .env file in a text editor. Fill in your actual credentials (Gmail App Password, Twilio SID/Token, Pushover Keys, etc.) for the alert services you want to use. SAVE THE FILE.
DO NOT COMMIT .env: The included .gitignore file should prevent you from accidentally committing your secrets if you use Git. Double-check this!
Configure Settings:

Edit config.py. Review all paths and settings.
Enable desired alerts: Set ENABLE_EMAIL_ALERT, ENABLE_SMS_ALERT, etc., to True.
Fill in necessary non-secret config values (sender/receiver emails, phone numbers, ntfy topic).
Adjust UNKNOWN_FRAMES_THRESHOLD and ALERT_COOLDOWN_SECONDS as needed.
Usage
Ensure your virtual environment is activated.

Prepare Known Faces: Populate the known_faces directory as described in the structure section (subfolders named after people, containing their images).
Run Face Encoder: Generate the encodings file.
Bash

python face_encoder.py
(Check logs/intruder_alert.log for output)
Run Intruder Detector: Start the main application. Ensure webcam is connected.
Bash

python intruder_detector.py
The webcam feed will display.
Faces will be boxed (Green=Known, Red=Unknown).
If an unknown face is detected for UNKNOWN_FRAMES_THRESHOLD consecutive processed frames, an alert will be triggered (subject to the ALERT_COOLDOWN_SECONDS).
An image of the intruder will be saved to the intruder_images/ directory.
Enabled alert channels (Email, SMS, App) will be notified. Check logs for confirmation or errors.
Press 'q' to quit.
Logging
Check the logs/intruder_alert.log file for detailed runtime information, warnings, and errors from all modules.
Log level is configurable in config.py.
Ethical Considerations & Limitations
Responsibility: Use this system ethically and legally. Respect privacy and obtain consent where applicable.
Bias: Face recognition can be biased. Test thoroughly for your use case.
False Positives/Negatives: The system might misidentify known people as "Unknown" or vice-versa. The threshold logic helps reduce false alerts, but tuning (MATCH_TOLERANCE, UNKNOWN_FRAMES_THRESHOLD) is likely needed.
Security: Storing API keys and passwords requires care. The .env method helps, but consider more robust secrets management for production systems. Protect the .pkl encoding file and saved intruder images.
Network Dependency: Alerts rely on internet connectivity and third-party service availability.
Cost: SMS messages via Twilio incur costs.
This system provides a proof-of-concept and requires careful tuning and consideration of limitations for real-world deployment.

License
MIT License recommended. Add a LICENSE file.


---

This provides a complete set of files for the Intruder Detection System. Remember to:
1.  Create the directory structure.
2.  Save each code block into its corresponding file name.
3.  Follow the **Setup** steps in the `README.md` very carefully, especially creating and populating the `.env` file for your credentials and **adding `.env` to `.gitignore`**.
4.  Configure `config.py` to enable the alerts you want and set parameters.
5.  Run the encoder, then the detector.