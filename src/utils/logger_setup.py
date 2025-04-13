# src/utils/logger_setup.py
import logging

def setup_logging():
    """Configures the root logger based on the original script's setup."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # No suppression added, keeping it exactly as the initial setup
    logging.info("Logging configured.")