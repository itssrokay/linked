# src/utils/logger_setup.py
import logging

def setup_logging():
    """Configures the root logger."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Suppress noisy logs from underlying libraries if needed
    # logging.getLogger("urllib3").setLevel(logging.WARNING)
    # logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.info("Logging configured.")