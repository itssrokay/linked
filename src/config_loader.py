# src/config_loader.py
import os
import json
import logging

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
        "max_pages": 1,
        "easy_apply_only": True
    },
    "output": {
        "save_to_file": True,
        "file_format": "json"
    }
}

def load_config(config_file_path="config/config.json"):
    """Loads configuration from a JSON file."""
    logging.info(f"Attempting to load configuration from: {config_file_path}")
    try:
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r', encoding='utf-8') as f:
                # Allow comments in JSON using a simple pre-processing step
                content = "".join(line for line in f if not line.strip().startswith("//"))
                config = json.loads(content)
            logging.info("Configuration loaded successfully from file.")
            # You might want to merge with defaults here to ensure all keys exist
            # merged_config = {**DEFAULT_CONFIG, **config} # Basic merge, might need deep merge
            return config
        else:
            logging.warning(f"Configuration file '{config_file_path}' not found. Using default settings.")
            return DEFAULT_CONFIG
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from {config_file_path}: {e}")
        logging.warning("Using default configuration settings.")
        return DEFAULT_CONFIG
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        logging.warning("Using default configuration settings.")
        return DEFAULT_CONFIG