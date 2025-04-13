# src/linkedin_actions/navigation.py
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Import helper from the utils directory
from ..utils.helpers import human_delay

# Define URL here or pass as argument
LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/"

# Directly copied from the provided code
def navigate_to_jobs_page(driver):
    """Navigates to the LinkedIn Jobs page."""
    logging.info("Navigating to the Jobs page...")
    try:
        driver.get(LINKEDIN_JOBS_URL)
        # Wait for jobs page to load - looking for the search boxes (using original selector)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='jobs-search-box-keyword-id']"))
        )
        human_delay() # Using helper
        logging.info("Successfully navigated to the Jobs page.")
        return True
    except TimeoutException:
        logging.error("Timed out waiting for the Jobs page to load.")
        return False
    except Exception as e:
        logging.error(f"Error navigating to Jobs page: {e}")
        return False