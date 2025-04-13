# src/config_loader.py
import os
import json
import logging

# Directly copied from the provided code
DEFAULT_CONFIG = {
    "search_criteria": {
        "keywords": "Python Developer",
        "location": "Bengaluru, Karnataka, India"
    },
    "filters": {
        "date_posted": "Past Week",
        "experience_level": ["Entry level", "Associate"]
    },
    "scraping": {
        "max_pages": 3,
        "easy_apply_only": True
    },
    "output": {
        "save_to_file": True,
        "file_format": "json"
    }
}

# Directly copied from the provided code
def load_config(config_file_path): # Accept the full path directly
    """Loads configuration from a JSON file."""
    logging.info(f"Loading configuration from: {config_file_path}")
    try:
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r') as f:
                # Use original json.load without comment handling for strict adherence
                config = json.load(f)
            logging.info("Configuration loaded successfully.")
            return config
        else:
            logging.warning(f"Configuration file {config_file_path} not found. Using default settings.")
            return DEFAULT_CONFIG
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        logging.warning("Using default configuration settings.")
        return DEFAULT_CONFIG