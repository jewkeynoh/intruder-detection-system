# Real-Time Intruder Detection System with Alerts

[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

This project leverages real-time facial recognition using Python, OpenCV, and the `face_recognition` library (built on dlib) to detect intruders via webcam. When an unknown face is persistently detected, it triggers alerts via Email, SMS (Twilio), and/or App Notifications (Pushover, ntfy.sh), optionally including an image of the intruder.

It offers robust modularity, alert customization, secure credential handling, and detailed logging, making it a practical surveillance tool for home or office use.

---

## Features

* **Known Face Learning**: Automatically encodes faces from images in the `known_faces/` directory.
* **Real-Time Face Detection**: Differentiates known from unknown individuals via webcam feed.
* **Persistent Unknown Detection**: Reduces false positives by requiring repeated detection of an unknown face.
* **Multi-Channel Alerting**: Supports Email, SMS, and push notifications.
* **Intruder Snapshot**: Captures and stores an image when an alert is triggered.
* **Centralized Config Management**: Easily adjust settings via `config.py`.
* **Credential Security**: Uses `.env` for storing sensitive API keys and credentials.
* **Verbose Logging**: Logs all detection and alert activity to file and console.
* **Modular Architecture**: Clean separation of components for encoding, detection, and alerting.

---

## Project Structure

```text
intruder_alert_system/
├── .gitignore
├── venv/
├── known_faces/
│   ├── Person1_Name/
│   │   └── image1.jpg
├── logs/
│   └── intruder_alert.log
├── intruder_images/
│   └── intruder_YYYYMMDD_HHMMSS.jpg
├── config.py
├── alert_utils.py
├── face_encoder.py
├── intruder_detector.py
├── requirements.txt
├── .env.example
├── .env
└── README.md
```

---

## Prerequisites

Before installing Python packages, ensure these system-level dependencies are installed:

* **Python 3.6+**
* **pip** (Python package manager)
* **CMake**: Required by dlib. Install via `apt`, `brew`, or from [cmake.org](https://cmake.org)
* **C++ Compiler**:

  * **Windows**: Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/), select *Desktop development with C++*.
  * **macOS**: Run `xcode-select --install`
  * **Linux**: `sudo apt install build-essential`

To verify:

```bash
cmake --version
```

Ensure CMake is in your PATH.

---

## Setup & Configuration

1. **Clone the Repository**

```bash
cd path/to/intruder_alert_system
```

2. **Create & Activate Virtual Environment**

```bash
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
```

3. **Install Python Dependencies**

```bash
pip install -r requirements.txt
```

4. **Set Up Environment Variables**

```bash
cp .env.example .env  # Linux/macOS
copy .env.example .env  # Windows
```

Edit `.env` to fill in actual API credentials (Google App Password, Twilio tokens, Pushover keys, etc.). Ensure `.env` is in `.gitignore`.

5. **Configure Settings**
   Edit `config.py` to:

* Enable or disable alert channels.
* Set thresholds like `MATCH_TOLERANCE`, `UNKNOWN_FRAMES_THRESHOLD`, and `ALERT_COOLDOWN_SECONDS`.
* Adjust file paths and deletion preferences.

---

## Usage

1. **Prepare Known Faces**
   Add labeled face images into `known_faces/Person_Name/` subfolders.

2. **Run Face Encoder**

```bash
python face_encoder.py
```

Creates `known_face_encodings.pkl`.

3. **Run Intruder Detection**

```bash
python intruder_detector.py
```

* Webcam window opens.
* Known faces = green box, Unknown = red box.
* Alerts triggered after configured unknown detection threshold.

---

## Troubleshooting

### Installation Issues

* **CMake/dlib Errors**: Recheck PATH and compiler tools.
* **Virtual Env Activation**: Use correct activation command for your shell.

### Alerts Not Working

* **Email**: Ensure 2FA is ON in your Google account and you're using an App Password.
* **SMS/Pushover**: Double-check API keys and tokens in `.env` and `config.py`.

### Recognition Inaccuracy

* Tune `MATCH_TOLERANCE`.
* Improve training image quality.
* Re-run `face_encoder.py` after changes.

### Webcam Not Working

* Try camera index `1` instead of `0`.
* Ensure no other application is using the webcam.

---

## Ethics & Privacy

Use this software responsibly and with consent in environments where surveillance is legally and ethically appropriate. Do not deploy in public spaces or without informing individuals being monitored.

---

## Future Improvements

* GUI interface for config and alert setup.
* Cloud upload of intruder snapshots.
* Mobile app integration for live feed.
* Face recognition model upgrades.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
