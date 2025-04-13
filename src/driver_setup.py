# src/driver_setup.py
import logging
import time
import random
from selenium import webdriver
# from selenium.webdriver.chrome.service import Service # Kept commented as in original logic if Selenium 4 manages automatically
# from webdriver_manager.chrome import ChromeDriverManager # Kept commented

# Directly copied from the provided code
def setup_driver():
    """Sets up the Chrome WebDriver."""
    logging.info("Setting up Chrome WebDriver...")
    try:
        options = webdriver.ChromeOptions()
        # Common options to help stability
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        # Anti-bot detection measures
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Emulate a regular user agent
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36") # Using the UA from your code

        # Set language
        options.add_argument("--lang=en-US")

        # Set window size
        options.add_argument("--window-size=1920,1080")

        # Create unique profile directory to avoid conflicts
        unique_dir = f"/tmp/chrome_profile_{int(time.time())}_{random.randint(1000, 9999)}"
        options.add_argument(f"--user-data-dir={unique_dir}")

        # Selenium 4+ automatically manages drivers
        driver = webdriver.Chrome(options=options)

        # Further anti-detection with JavaScript execution
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        logging.info("WebDriver setup successful.")
        return driver
    except Exception as e:
        logging.error(f"Error setting up WebDriver: {e}")
        return None