# -*- coding: utf-8 -*-
"""
Real-time Intruder Detection using Face Recognition.

Captures video from webcam, detects known/unknown faces, and triggers
alerts via configured notification channels when an unknown face is
persistently detected.
"""

import face_recognition
import cv2
import pickle
import numpy as np
import logging
import sys
import time
import datetime
import threading
import os
from pathlib import Path

# Import configuration and alert utilities
try:
    import config
    import alert_utils # Import our alert functions
except ImportError as e:
    print(f"[CRITICAL ERROR] Failed to import required modules (config.py or alert_utils.py): {e}")
    print("Ensure config.py and alert_utils.py are in the same directory or Python path.")
    sys.exit(1)

# --- Setup Logging ---
logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE), # Log to file
        logging.StreamHandler() # Log to console
    ]
)
logger = logging.getLogger(__name__) # Get logger for this module

# --- Load OpenCV Font ---
try:
    CV2_FONT = getattr(cv2, config.CV2_FONT_NAME)
except AttributeError:
    logger.warning(f"Could not find OpenCV font '{config.CV2_FONT_NAME}'. Falling back to FONT_HERSHEY_SIMPLEX.")
    CV2_FONT = cv2.FONT_HERSHEY_SIMPLEX


def load_known_encodings(filepath):
    """Loads known face encodings and names from a pickle file."""
    logger.info(f"Loading known face encodings from {filepath}...")
    if not filepath.is_file():
        logger.error(f"Encodings file not found: {filepath}")
        logger.error("Please run the face_encoder.py script first.")
        return None, None
    try:
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        if "encodings" not in data or "names" not in data:
             logger.error(f"Invalid data structure in encodings file: {filepath}")
             return None, None

        known_encodings = data["encodings"]
        known_names = data["names"]

        if not known_encodings or not known_names:
            logger.warning(f"No encodings or names loaded from {filepath}.")
            return [], [] # Return empty lists if file was valid but empty

        logger.info(f"Loaded {len(known_names)} known encodings.")
        return known_encodings, known_names

    except pickle.UnpicklingError as e:
        logger.error(f"Failed to unpickle encodings file {filepath}: {e}")
        return None, None
    except Exception as e:
        logger.error(f"An unexpected error occurred loading encodings: {e}", exc_info=True)
        return None, None


def initialize_webcam(source=0):
    """Initializes and returns the webcam video capture object."""
    logger.info(f"Initializing video capture source: {source}...")
    video_capture = cv2.VideoCapture(source)
    if not video_capture.isOpened():
        logger.critical(f"Could not open video source: {source}. Check camera connection/permissions.")
        return None
    logger.info("Video capture initialized successfully.")
    return video_capture


def process_frame_for_faces(frame, known_encodings, known_names):
    """Detects and recognizes faces in a single video frame."""
    # Resize for speed
    if config.FRAME_PROCESS_SCALE != 1.0:
        small_frame = cv2.resize(frame, (0, 0), fx=config.FRAME_PROCESS_SCALE, fy=config.FRAME_PROCESS_SCALE)
        scale_factor = 1.0 / config.FRAME_PROCESS_SCALE
    else:
        small_frame = frame
        scale_factor = 1.0

    # Convert BGR to RGB
    try:
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    except cv2.error as e:
        logger.error(f"OpenCV error during color conversion: {e}")
        return [], [], scale_factor # Return empty if conversion fails

    # Detect Faces
    try:
        face_locations_small = face_recognition.face_locations(
            rgb_small_frame,
            model=config.DETECTION_MODEL,
            number_of_times_to_upsample=config.UPSAMPLE_TIMES
        )
        # Encode Faces
        face_encodings = face_recognition.face_encodings(
            rgb_small_frame,
            known_face_locations=face_locations_small,
            num_jitters=config.NUM_JITTERS
        )
    except Exception as e:
        logger.error(f"Error during face detection/encoding: {e}", exc_info=False) # Reduce log noise
        return [], [], scale_factor

    # Match Faces
    detected_names = []
    if not known_encodings: # Handle case where no known faces are loaded
        detected_names = ["Unknown"] * len(face_encodings)
    else:
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(
                known_encodings,
                face_encoding,
                tolerance=config.MATCH_TOLERANCE
            )
            name = "Unknown"
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            if face_distances.size > 0: # Check if face_distances is not empty
                 best_match_index = np.argmin(face_distances)
                 if matches[best_match_index] and face_distances[best_match_index] < config.MATCH_TOLERANCE:
                     name = known_names[best_match_index]
                     logger.debug(f"Match: {name} (Dist: {face_distances[best_match_index]:.2f})")
            detected_names.append(name)

    return face_locations_small, detected_names, scale_factor


def draw_detections(frame, face_locations_small, detected_names, scale_factor):
    """Draws bounding boxes and names onto the frame."""
    for (top, right, bottom, left), name in zip(face_locations_small, detected_names):
        # Scale back up face locations
        top = int(top * scale_factor)
        right = int(right * scale_factor)
        bottom = int(bottom * scale_factor)
        left = int(left * scale_factor)

        is_known = name != "Unknown"
        box_color = config.BOX_COLOR_KNOWN if is_known else config.BOX_COLOR_UNKNOWN
        text_color = config.TEXT_COLOR_KNOWN if is_known else config.TEXT_COLOR_UNKNOWN

        # Draw bounding box
        cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)

        # Draw label background and text
        label_y = bottom - 15
        if top < 30: label_y = bottom + 15 # Adjust if box is near top

        try:
            # Ensure label background height scales roughly with font size
            label_height = int(config.FONT_SCALE * 30)
            cv2.rectangle(frame, (left, label_y - label_height), (right, bottom), box_color, cv2.FILLED)
            # Adjust text position based on calculated label background height
            text_y = bottom - int(label_height * 0.25) # Position text roughly in the middle of the label bg
            cv2.putText(frame, name, (left + 6, text_y), CV2_FONT, config.FONT_SCALE, text_color, config.FONT_THICKNESS)
        except Exception as e:
            logger.error(f"Error drawing text/rectangle: {e}")


def run_intruder_detection():
    """Main loop for intruder detection and alerting."""
    logger.info("Starting Intruder Detection System...")

    known_encodings, known_names = load_known_encodings(config.ENCODINGS_PATH)
    if known_encodings is None:
        logger.critical("Failed to load known encodings. Exiting.")
        return

    video_capture = initialize_webcam(0) # Use 0 for default webcam
    if video_capture is None:
        logger.critical("Failed to initialize webcam. Exiting.")
        return

    # --- State Variables for Intruder Logic ---
    unknown_detected_frames_count = 0
    alert_triggered_for_current_event = False
    last_alert_timestamp = 0
    # Keep track of last known locations/names to display between processed frames
    last_face_locations = []
    last_detected_names = []
    last_scale_factor = 1.0

    frame_number = 0
    prev_frame_time = 0

    while True:
        ret, frame = video_capture.read()
        if not ret:
            logger.error("Failed to grab frame from video source. Exiting loop.")
            break

        current_time = time.time()

        # --- Process Frame (every Nth frame) ---
        if frame_number % config.PROCESS_EVERY_N_FRAMES == 0:
            # Process the frame
            face_locations_small, detected_names, scale_factor = process_frame_for_faces(
                frame, known_encodings, known_names
            )
            # Update last known state
            last_face_locations = face_locations_small
            last_detected_names = detected_names
            last_scale_factor = scale_factor

            logger.debug(f"Frame {frame_number}: Processed. Faces: {len(detected_names)}. Names: {detected_names}")

            # --- Intruder Detection Logic ---
            is_unknown_present_in_frame = "Unknown" in detected_names

            if is_unknown_present_in_frame:
                unknown_detected_frames_count += 1
                logger.debug(f"Unknown detected. Consecutive count: {unknown_detected_frames_count}")
            else:
                # Reset if no unknown face seen in this processed frame
                if unknown_detected_frames_count > 0:
                     logger.info("Unknown face event ended. Resetting counter.")
                unknown_detected_frames_count = 0
                alert_triggered_for_current_event = False # Allow new alert if unknown appears again

            # --- Alert Trigger ---
            if (unknown_detected_frames_count >= config.UNKNOWN_FRAMES_THRESHOLD and
                    not alert_triggered_for_current_event and
                    (current_time - last_alert_timestamp) > config.ALERT_COOLDOWN_SECONDS):

                logger.warning(f"ALERT TRIGGERED: Unknown face detected for {unknown_detected_frames_count} frames.")
                alert_triggered_for_current_event = True # Don't trigger again for this continuous event
                last_alert_timestamp = current_time
                # Keep counter going? Or reset? Resetting detects *next* persistent event.
                # unknown_detected_frames_count = 0 # Reset to detect next N frames

                # Save image and send alerts in a separate thread
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"intruder_{timestamp}.jpg"
                image_path = config.INTRUDER_IMAGE_DIR / filename

                try:
                    # Save the current full-resolution frame
                    cv2.imwrite(str(image_path), frame)
                    logger.info(f"Saved intruder image: {image_path}")

                    # Prepare alert details
                    subject = "Intruder Alert Detected!"
                    text_body = f"Unknown person detected at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
                    sms_body = f"Intruder Alert at {datetime.datetime.now().strftime('%H:%M:%S')}!" # Shorter for SMS

                    # Start alert thread
                    alert_thread = threading.Thread(
                        target=alert_utils.trigger_notifications,
                        args=(subject, text_body, sms_body, image_path),
                        daemon=True # Allows main program to exit even if alert thread hangs (optional)
                    )
                    alert_thread.start()

                except Exception as e:
                    logger.error(f"Failed to save image or start alert thread: {e}", exc_info=True)
        else:
             # Frame skipped processing, use last known results for display
             logger.debug(f"Frame {frame_number}: Skipped processing.")
             pass


        # --- Draw Detections on Frame (using last known results) ---
        draw_detections(frame, last_face_locations, last_detected_names, last_scale_factor)

        # --- Calculate and Draw FPS ---
        if prev_frame_time != 0:
            fps = 1.0 / (current_time - prev_frame_time)
            fps_text = f"FPS: {fps:.1f}"
            try:
                 cv2.putText(frame, fps_text, config.FPS_POSITION, CV2_FONT, config.FONT_SCALE, config.TEXT_COLOR_KNOWN, config.FONT_THICKNESS)
            except Exception as e:
                logger.error(f"Error drawing FPS: {e}")
        prev_frame_time = current_time

        # --- Display Frame ---
        try:
            cv2.imshow('Intruder Detection System', frame)
        except Exception as e:
            logger.error(f"cv2.imshow error: {e}. Exiting loop.")
            break

        frame_number += 1

        # --- Exit Condition ---
        if cv2.waitKey(1) & 0xFF == ord('q'):
            logger.info("Exit key 'q' pressed. Shutting down.")
            break

    # --- Cleanup ---
    logger.info("Releasing video capture and destroying windows.")
    if video_capture: video_capture.release()
    cv2.destroyAllWindows()
    logger.info("Intruder Detection System stopped.")


def main():
    """Main execution function."""
    # Setup directories (config.py should handle this, but double-check)
    try:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        config.INTRUDER_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.critical(f"Failed to ensure necessary directories exist: {e}")
        return # Exit if we can't create essential folders

    run_intruder_detection()


if __name__ == "__main__":
    main()