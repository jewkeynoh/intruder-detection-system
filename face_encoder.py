# -*- coding: utf-8 -*-
"""
Encodes known faces from image files and saves the encodings.

This script processes images found in the specified known faces directory,
detects faces, generates encodings for each detected face (if exactly one
face is found per image), and saves the encodings along with their
corresponding names to a pickle file for later use in face recognition.
"""

import face_recognition
import pickle
import logging
from pathlib import Path
import sys
import time # To measure encoding time

# Import configuration settings
try:
    import config
except ImportError:
    print("[ERROR] config.py not found. Please ensure it's in the same directory or Python path.")
    sys.exit(1)

# --- Setup Logging ---
logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler() # Also print logs to console
    ]
)

def setup_directories():
    """Ensures necessary directories exist."""
    try:
        config.KNOWN_FACES_DIR.mkdir(parents=True, exist_ok=True)
        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        logging.info(f"Checked/created necessary directories.")
        logging.info(f"Expecting known faces in: {config.KNOWN_FACES_DIR}")
        logging.info(f"Encodings will be saved to: {config.ENCODINGS_PATH}")
    except OSError as e:
        logging.critical(f"Failed to create necessary directories: {e}")
        sys.exit(1)

def encode_known_faces():
    """
    Loads images from the known faces directory, encodes faces, and returns data.

    Iterates through subdirectories (each representing a person) in the
    KNOWN_FACES_DIR. For each image file found, it attempts to load the image,
    detect exactly one face, and compute its encoding.

    Returns:
        tuple: A tuple containing:
            - list: A list of face encodings (numpy arrays).
            - list: A list of corresponding names (strings).
    """
    logging.info(f"Starting face encoding process from directory: {config.KNOWN_FACES_DIR}")
    known_face_encodings = []
    known_face_names = []
    processed_image_count = 0
    encoded_face_count = 0
    start_time = time.time()

    # Check if the known faces directory exists
    if not config.KNOWN_FACES_DIR.is_dir():
        logging.error(f"Known faces directory not found: {config.KNOWN_FACES_DIR}")
        logging.error("Please create it and add subdirectories with images for each known person.")
        return [], []

    # Iterate through each person's directory
    for person_dir in config.KNOWN_FACES_DIR.iterdir():
        if person_dir.is_dir():
            person_name = person_dir.name
            logging.info(f"Processing images for: {person_name}")

            # Iterate through each image file for the person
            for image_file in person_dir.iterdir():
                # Check if it's a file and has a common image extension
                if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                    processed_image_count += 1
                    logging.debug(f"Processing image: {image_file.name}")

                    try:
                        # Load image file
                        image = face_recognition.load_image_file(image_file)

                        # Find face locations using the configured model
                        # We expect exactly one face per 'known' image for simplicity
                        face_locations = face_recognition.face_locations(
                            image,
                            model=config.DETECTION_MODEL,
                            number_of_times_to_upsample=config.UPSAMPLE_TIMES
                        )

                        # Validate number of faces found
                        if len(face_locations) == 1:
                            # Calculate face encoding
                            # Use known_face_locations to speed up encoding if locations are already found
                            face_encodings = face_recognition.face_encodings(
                                image,
                                known_face_locations=face_locations,
                                num_jitters=config.NUM_JITTERS
                            )

                            if face_encodings: # Should always have one if locations=1
                                known_face_encodings.append(face_encodings[0])
                                known_face_names.append(person_name)
                                encoded_face_count += 1
                                logging.debug(f"Successfully encoded face from {image_file.name}")
                            else:
                                # This case should be rare if face_locations found one face
                                logging.warning(f"Could not encode face despite finding location in {image_file.name}. Skipping.")

                        elif len(face_locations) == 0:
                            logging.warning(f"No faces found in {image_file.name}. Skipping.")
                        else:
                            logging.warning(f"Found {len(face_locations)} faces in {image_file.name}. Expected 1. Skipping.")

                    except FileNotFoundError:
                        logging.error(f"Image file not found (should not happen with iterdir): {image_file}")
                    except Exception as e:
                        # Catch other potential errors (PIL issues, memory errors, etc.)
                        logging.error(f"Failed to process image {image_file.name}: {e}")
                else:
                    logging.debug(f"Skipping non-image file or unsupported extension: {image_file.name}")

    end_time = time.time()
    duration = end_time - start_time
    logging.info(f"Finished face encoding process in {duration:.2f} seconds.")
    logging.info(f"Processed {processed_image_count} images.")
    logging.info(f"Successfully encoded {encoded_face_count} faces for {len(set(known_face_names))} unique individuals.")

    if not known_face_encodings:
        logging.warning("No faces were successfully encoded. The encodings file will be empty or not created.")

    return known_face_encodings, known_face_names

def save_encodings(known_face_encodings, known_face_names, filepath):
    """
    Saves the face encodings and names to a pickle file.

    Args:
        known_face_encodings (list): List of face encodings (numpy arrays).
        known_face_names (list): List of corresponding names.
        filepath (Path): The path object where the pickle file will be saved.
    """
    if not known_face_encodings:
        logging.warning("No encodings to save.")
        # Optionally delete old file if it exists? Or just overwrite with empty?
        # Let's overwrite for simplicity here.
        # return

    logging.info(f"Saving encodings for {len(known_face_names)} faces to {filepath}...")
    encodings_data = {"encodings": known_face_encodings, "names": known_face_names}

    try:
        with open(filepath, "wb") as f:
            pickle.dump(encodings_data, f)
        logging.info("Encodings saved successfully.")
    except IOError as e:
        logging.critical(f"Failed to write encodings file to {filepath}: {e}")
        sys.exit(1)
    except pickle.PicklingError as e:
         logging.critical(f"Failed to pickle encoding data: {e}")
         sys.exit(1)

def main():
    """Main function to run the encoding process."""
    setup_directories()
    known_encodings, known_names = encode_known_faces()
    if known_encodings: # Only save if we actually encoded something
         save_encodings(known_encodings, known_names, config.ENCODINGS_PATH)
    else:
         logging.error("Encoding process finished, but no faces were encoded.")
         # Decide if an empty file should still be saved
         # save_encodings([], [], config.ENCODINGS_PATH) # Uncomment to save empty file


if __name__ == "__main__":
    # This block ensures the main function runs only when the script is executed directly
    main()