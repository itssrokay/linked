# src/driver_setup.py
import logging
import time
import random
from selenium import webdriver
# from selenium.webdriver.chrome.service import Service  # Uncomment if using Service object explicitly
# from webdriver_manager.chrome import ChromeDriverManager # Uncomment if needed

def setup_driver(profile_dir_base="/tmp/chrome_profiles"):
    """Sets up the Chrome WebDriver with anti-detection measures."""
    logging.info("Setting up Chrome WebDriver...")
    try:
        options = webdriver.ChromeOptions()
        # Common options
        options.add_argument("--no-sandbox") # Necessary for Docker/Linux environments
        options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
        options.add_argument("--disable-gpu") # May improve performance/stability
        options.add_argument("--window-size=1920,1080") # Set a common resolution
        options.add_argument("--lang=en-US") # Set language

        # Anti-bot detection measures
        options.add_argument("--disable-blink-features=AutomationControlled") # Hides the 'navigator.webdriver' flag
        options.add_experimental_option("excludeSwitches", ["enable-automation"]) # Removes "Chrome is being controlled..." banner
        options.add_experimental_option('useAutomationExtension', False) # Disables automation extension

        # Emulate a realistic user agent
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36" # Example UA, update periodically
        )

        # # Optional: Use a persistent profile directory for cookies/sessions
        # # Create a unique directory for this session to avoid conflicts if running multiple instances
        # unique_profile_dir = f"{profile_dir_base}/profile_{int(time.time())}_{random.randint(1000, 9999)}"
        # options.add_argument(f"--user-data-dir={unique_profile_dir}")
        # logging.info(f"Using profile directory: {unique_profile_dir}")

        # Optional: Headless mode
        # options.add_argument("--headless")

        # Selenium 4+ often manages drivers automatically.
        # If explicit management is needed:
        # service = Service(ChromeDriverManager().install())
        # driver = webdriver.Chrome(service=service, options=options)
        driver = webdriver.Chrome(options=options)

        # Further anti-detection with JavaScript execution (after driver is created)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        logging.info("WebDriver setup successful.")
        return driver
    except Exception as e:
        logging.error(f"Error setting up WebDriver: {e}")
        # Log specific webdriver errors if possible
        if "session not created" in str(e):
            logging.error("Common cause: ChromeDriver version mismatch with installed Chrome browser or permission issues.")
        return None