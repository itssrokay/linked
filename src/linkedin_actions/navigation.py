# src/linkedin_actions/navigation.py
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from ..utils.helpers import human_delay

LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/"

def navigate_to_jobs_page(driver):
    """Navigates to the LinkedIn Jobs page after login."""
    logging.info("Navigating to the Jobs page...")
    try:
        # Try clicking the 'Jobs' icon first - more robust if URL changes
        jobs_icon_xpath = "//a[contains(@href, '/jobs/')][@data-link-to='jobs'] | //li-icon[@type='job']//ancestor::a"
        jobs_icon = WebDriverWait(driver, 15).until(
             EC.element_to_be_clickable((By.XPATH, jobs_icon_xpath))
        )
        jobs_icon.click()
        logging.info("Clicked 'Jobs' icon.")

    except Exception as e:
        logging.warning(f"Could not click 'Jobs' icon ({e}). Falling back to direct URL navigation.")
        try:
             driver.get(LINKEDIN_JOBS_URL)
        except Exception as nav_e:
             logging.error(f"Failed to navigate to Jobs page via URL: {nav_e}")
             return False


    # Wait for jobs page main elements to load
    try:
        # Wait for either the keyword or location search box
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='jobs-search-box-keyword-id'], input[id*='jobs-search-box-location-id']"))
        )
        human_delay(1, 2) # Allow page to settle
        logging.info("Successfully navigated to the Jobs page.")
        return True
    except TimeoutException:
        logging.error("Timed out waiting for the main Jobs page elements (search boxes) to load.")
        # Save debug info
        try:
            driver.save_screenshot(f"debug_jobs_page_timeout_{time.strftime('%Y%m%d%H%M%S')}.png")
        except: pass
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred navigating to Jobs page: {e}")
        return False