import os
import time
import random
import logging
import json
import pickle
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, \
    StaleElementReferenceException

# --- Configuration ---
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Load environment variables
load_dotenv()
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/"

# Default configuration
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


# --- Helper Functions ---
def human_delay(min_seconds=1.0, max_seconds=3.0):
    """Adds a random delay to mimic human behavior."""
    time.sleep(random.uniform(min_seconds, max_seconds))


def human_like_scroll(driver, scroll_amount=None):
    """Scrolls the page in a human-like way."""
    if scroll_amount is None:
        scroll_amount = random.randint(300, 700)

    # Break scrolling into multiple small movements
    steps = random.randint(3, 7)
    for i in range(steps):
        step_scroll = scroll_amount // steps
        variation = random.randint(-20, 20)  # Add some variation
        driver.execute_script(f"window.scrollBy(0, {step_scroll + variation})")
        time.sleep(random.uniform(0.1, 0.3))


def load_config(config_file="config.json"):
    """Loads configuration from a JSON file."""
    logging.info(f"Loading configuration from: {config_file}")
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            logging.info("Configuration loaded successfully.")
            return config
        else:
            logging.warning(f"Configuration file {config_file} not found. Using default settings.")
            return DEFAULT_CONFIG
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        logging.warning("Using default configuration settings.")
        return DEFAULT_CONFIG


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
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")

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


def login_to_linkedin(driver, email, password):
    """Logs into LinkedIn using provided credentials."""
    if not driver:
        logging.error("WebDriver not initialized. Cannot proceed.")
        return False

    logging.info(f"Navigating to LinkedIn login page: {LINKEDIN_LOGIN_URL}")
    try:
        driver.get(LINKEDIN_LOGIN_URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        logging.info("Login page loaded.")
    except TimeoutException:
        logging.error("Timed out waiting for the LinkedIn login page to load.")
        return False
    except Exception as e:
        logging.error(f"Error navigating to login page: {e}")
        return False

    try:
        logging.info("Attempting to log in...")
        # Find username/email field and enter email
        username_field = driver.find_element(By.ID, "username")
        username_field.clear()
        username_field.send_keys(email)
        human_delay(0.8, 1.5)

        # Find password field and enter password
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(password)
        human_delay(0.8, 1.5)

        # Find and click the login button
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        login_button.click()
        logging.info("Login button clicked.")
        logging.info("Waiting for page transition after login click...")

        # Wait for either the feed page or a potential security check/error page
        WebDriverWait(driver, 20).until(
            lambda d: "feed" in d.current_url or
                      "checkpoint" in d.current_url or
                      "challenge" in d.current_url or
                      "/login" not in d.current_url
        )

        current_url = driver.current_url
        logging.info(f"URL after login attempt: {current_url}")

        if "feed" in current_url:
            logging.info("Login Successful! Redirected to the feed.")
            return True
        elif "checkpoint" in current_url or "challenge" in current_url:
            logging.warning(
                "Login Alert: LinkedIn is asking for a security check (CAPTCHA, phone verification, etc.).")
            logging.info("Please complete the verification in the browser window...")
            input("Press Enter after completing the verification manually...")
            if "feed" in driver.current_url:
                logging.info("Verification successful! Now on feed.")
                return True
            return False
        elif "/login" in current_url:
            try:
                error_msg = driver.find_element(By.ID, "error-for-password")
                if error_msg.is_displayed():
                    logging.error(f"Login Failed: {error_msg.text}")
                    return False
            except NoSuchElementException:
                logging.error("Login Failed: Still on login page, but no specific error message found.")
                return False
            except Exception as e:
                logging.error(f"Login Failed: Error checking for login failure messages: {e}")
                return False
        else:
            logging.warning(f"Login Status Uncertain: Redirected to {current_url}")
            return True

    except TimeoutException as e:
        logging.error(f"Login Error: Timed out waiting for an element during login. {e}")
        return False
    except NoSuchElementException as e:
        logging.error(
            f"Login Error: Could not find an element (username, password, or login button). LinkedIn UI might have changed. {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during login: {e}")
        return False


def login_with_retry(driver, email, password, max_attempts=2):
    """Attempt to login multiple times in case of transient failures."""
    for attempt in range(1, max_attempts + 1):
        logging.info(f"Login attempt {attempt}/{max_attempts}")
        if login_to_linkedin(driver, email, password):
            logging.info("\nLogin successful. Proceeding...\n")
            return True

        if attempt < max_attempts:
            wait_time = 5 * attempt  # Progressive backoff
            logging.info(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)

            # If we were redirected to an unexpected page, go back to login
            if "/login" not in driver.current_url:
                logging.info("Navigating back to login page for retry...")
                driver.get(LINKEDIN_LOGIN_URL)
                time.sleep(2)

    logging.error(f"Failed to login after {max_attempts} attempts.")
    return False


def navigate_to_jobs_page(driver):
    """Navigates to the LinkedIn Jobs page."""
    logging.info("Navigating to the Jobs page...")
    try:
        driver.get(LINKEDIN_JOBS_URL)
        # Wait for jobs page to load - looking for the search boxes
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='jobs-search-box-keyword-id']"))
        )
        human_delay()
        logging.info("Successfully navigated to the Jobs page.")
        return True
    except TimeoutException:
        logging.error("Timed out waiting for the Jobs page to load.")
        return False
    except Exception as e:
        logging.error(f"Error navigating to Jobs page: {e}")
        return False


def perform_job_search(driver, keywords, location):
    """Enters search keywords and location and initiates the search."""
    logging.info(f"Performing job search for Keywords: '{keywords}', Location: '{location}'")
    try:
        # Find keyword input field
        keyword_input_selector = "input[id*='jobs-search-box-keyword-id']"
        keyword_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, keyword_input_selector))
        )
        keyword_input.clear()
        keyword_input.send_keys(keywords)
        human_delay(0.5, 1.0)

        # Find location input field
        location_input_selector = "input[id*='jobs-search-box-location-id']"
        location_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, location_input_selector))
        )
        # Clear location field thoroughly
        location_input.send_keys(Keys.CONTROL + "a")
        location_input.send_keys(Keys.BACKSPACE)
        human_delay(0.3, 0.7)
        location_input.send_keys(location)
        human_delay(1.0, 2.0)  # Allow time for suggestions
        location_input.send_keys(Keys.ENTER)  # Submit search via Enter key
        logging.info("Search criteria entered. Submitted search via Enter key.")

        # --- Wait for results page to load with multiple detection strategies ---
        logging.info("Waiting for search results page to load...")

        # Define multiple possible selectors for detecting the results page
        possible_selectors = [
            # Primary structure (original selector)
            {"type": "css", "value": "div.scaffold-layout__list > ul", "name": "Job list container"},
            # Alternative structures
            {"type": "css", "value": ".jobs-search-results-list", "name": "Jobs results list"},
            {"type": "css", "value": ".scaffold-layout__list", "name": "Scaffold layout list"},
            {"type": "xpath", "value": "//div[contains(@class, 'jobs-search-results')]",
             "name": "Jobs search results div"},
            # Fallback indicators
            {"type": "css", "value": ".jobs-search-no-results", "name": "No results indicator"},
            {"type": "xpath", "value": "//button[contains(text(), 'Date posted')]",
             "name": "Date posted filter button"},
            {"type": "xpath", "value": "//li[contains(@class, 'jobs-search-results__list-item')]",
             "name": "Any job list item"},
            # Additional LinkedIn 2025 selectors
            {"type": "xpath", "value": "//div[contains(@class, 'jobs-search-results-grid')]",
             "name": "Jobs results grid"}
        ]

        # Try each selector with a short timeout
        for selector in possible_selectors:
            try:
                logging.info(f"Trying to locate {selector['name']}: {selector['value']}")
                if selector['type'] == 'css':
                    WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector['value']))
                    )
                else:
                    WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.XPATH, selector['value']))
                    )
                logging.info(f"Search results page detected using {selector['name']}!")
                human_delay()
                return True
            except TimeoutException:
                logging.warning(f"Could not find {selector['name']} within timeout")
                continue

        # If direct selectors don't work, try a URL-based approach
        try:
            logging.info("Trying URL-based detection...")
            WebDriverWait(driver, 10).until(
                lambda d: "jobs/search" in d.current_url
            )
            logging.info("Job search URL detected. Assuming results page loaded.")
            # Take a screenshot for debugging
            screenshot_path = f"job_search_results_{time.strftime('%Y%m%d%H%M%S')}.png"
            driver.save_screenshot(screenshot_path)
            logging.info(f"Saved screenshot to {screenshot_path}")
            human_delay()
            return True
        except TimeoutException:
            logging.warning("URL-based detection also failed")

        # Final fallback: check if page structure changed significantly
        logging.info("Trying generic page change detection...")
        old_source_len = len(driver.page_source)
        human_delay(5.0, 7.0)  # Wait longer
        new_source_len = len(driver.page_source)

        if abs(new_source_len - old_source_len) > 5000:  # Significant change threshold
            logging.info("Page content changed significantly. Assuming results loaded.")
            screenshot_path = f"generic_change_results_{time.strftime('%Y%m%d%H%M%S')}.png"
            driver.save_screenshot(screenshot_path)
            logging.info(f"Saved screenshot to {screenshot_path}")
            return True

        # If all detection methods fail
        logging.error("None of the detection methods could identify the search results page")

        # Save debug information
        debug_filename = f"debug_page_source_search_fail_{time.strftime('%Y%m%d%H%M%S')}.html"
        with open(debug_filename, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info(f"Saved page source to {debug_filename}")

        # Take one final screenshot
        screenshot_path = f"failed_search_results_{time.strftime('%Y%m%d%H%M%S')}.png"
        driver.save_screenshot(screenshot_path)
        logging.info(f"Saved screenshot to {screenshot_path}")

        return False

    except Exception as e:
        logging.error(f"An unexpected error occurred during job search: {e}")
        # Try to save debug information even on exception
        try:
            debug_filename = f"exception_search_fail_{time.strftime('%Y%m%d%H%M%S')}.html"
            with open(debug_filename, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logging.info(f"Saved exception page source to {debug_filename}")
        except:
            pass
        return False


def apply_filters(driver, date_posted=None, experience_levels=None):
    """Applies filters to the job search results."""
    logging.info("Applying filters...")
    filters_applied = False

    # Wait for page to stabilize after search
    human_delay(3.0, 5.0)

    # ---- Apply Date Posted filter ----
    if date_posted:
        try:
            logging.info(f"Applying 'Date Posted' filter: {date_posted}")

            # Try multiple approaches to find and click the date filter button
            date_filter_button_selectors = [
                "//button[contains(text(), 'Date posted')]",
                "//button[contains(@aria-label, 'Date posted')]",
                "//button[contains(@id, 'date-posted')]",
                "//div[text()='Date posted']//ancestor::button",
                "//span[text()='Date posted']//ancestor::button"
            ]

            date_button = None
            for selector in date_filter_button_selectors:
                try:
                    date_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except:
                    continue

            if not date_button:
                logging.warning("Could not find Date Posted filter button. Skipping this filter.")
                # Take screenshot for debugging
                driver.save_screenshot(f"date_filter_not_found_{time.strftime('%Y%m%d%H%M%S')}.png")
            else:
                # Try to click the button, with retry for potential overlays
                try:
                    date_button.click()
                except ElementClickInterceptedException:
                    # Try to dismiss any overlays or use JavaScript click
                    driver.execute_script("arguments[0].click();", date_button)

                human_delay()

                # Try to find the option by multiple approaches
                option_found = False

                # Method 1: Standard checkbox approach
                try:
                    option_labels = [
                        f"//label[contains(text(), '{date_posted}')]",
                        f"//span[contains(text(), '{date_posted}')]/ancestor::label",
                        f"//div[contains(text(), '{date_posted}')]/ancestor::label"
                    ]

                    for label_xpath in option_labels:
                        try:
                            option_label = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, label_xpath))
                            )
                            option_label.click()
                            human_delay()
                            option_found = True
                            break
                        except:
                            continue
                except Exception as e:
                    logging.warning(f"Error with standard checkbox approach: {e}")

                # Method 2: Dropdown selection
                if not option_found:
                    try:
                        dropdown_items = driver.find_elements(By.XPATH,
                                                              f"//div[contains(@role, 'menuitem')][contains(text(), '{date_posted}')]")
                        if dropdown_items:
                            dropdown_items[0].click()
                            option_found = True
                            human_delay()
                    except Exception as e:
                        logging.warning(f"Error with dropdown selection approach: {e}")

                # Method 3: Try buttons in a dialog
                if not option_found:
                    try:
                        buttons = driver.find_elements(By.XPATH, f"//button[contains(text(), '{date_posted}')]")
                        if buttons:
                            buttons[0].click()
                            option_found = True
                            human_delay()
                    except Exception as e:
                        logging.warning(f"Error with button selection approach: {e}")

                # Close the filter dialog if needed (Apply button or Done button)
                try:
                    apply_buttons = driver.find_elements(By.XPATH,
                                                         "//button[contains(text(), 'Apply') or contains(text(), 'Done') or contains(text(), 'Show results')]")
                    if apply_buttons:
                        apply_buttons[0].click()
                        human_delay()
                except Exception as e:
                    logging.warning(f"Error clicking apply/done button: {e}")

                # If all methods failed
                if not option_found:
                    logging.warning(f"Could not find or select '{date_posted}' option.")
                    driver.save_screenshot(f"date_option_not_found_{time.strftime('%Y%m%d%H%M%S')}.png")
                else:
                    filters_applied = True
        except Exception as e:
            logging.error(f"Error applying 'Date Posted' filter: {e}")

    # ---- Apply Experience Level filter ----
    if experience_levels and len(experience_levels) > 0:
        logging.info(f"Applying 'Experience Level' filter(s): {', '.join(experience_levels)}")
        try:
            # Try to find and click the Experience Level filter button
            exp_filter_button_selectors = [
                "//button[contains(text(), 'Experience level')]",
                "//button[contains(@aria-label, 'Experience level')]",
                "//button[contains(@id, 'experience-level')]",
                "//div[text()='Experience level']//ancestor::button",
                "//span[text()='Experience level']//ancestor::button"
            ]

            exp_button = None
            for selector in exp_filter_button_selectors:
                try:
                    exp_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except:
                    continue

            if not exp_button:
                logging.warning("Could not find Experience Level filter button. Skipping this filter.")
                # Take screenshot for debugging
                driver.save_screenshot(f"exp_filter_not_found_{time.strftime('%Y%m%d%H%M%S')}.png")
            else:
                # Try to click the button, with retry for potential overlays
                try:
                    exp_button.click()
                except ElementClickInterceptedException:
                    # Try with JavaScript
                    driver.execute_script("arguments[0].click();", exp_button)

                human_delay()

                # Try to select each experience level
                for exp_level in experience_levels:
                    try:
                        # Find the checkbox/label by multiple approaches
                        selectors = [
                            f"//label[contains(text(), '{exp_level}')]",
                            f"//span[contains(text(), '{exp_level}')]/ancestor::label",
                            f"//div[contains(text(), '{exp_level}')]/ancestor::label",
                            f"//div[contains(@role, 'menuitem')][contains(text(), '{exp_level}')]"
                        ]

                        checkbox_found = False
                        for selector in selectors:
                            try:
                                elements = driver.find_elements(By.XPATH, selector)
                                if elements:
                                    # Click the first matching element
                                    elements[0].click()
                                    checkbox_found = True
                                    human_delay(0.5, 1.0)
                                    break
                            except:
                                continue

                        if not checkbox_found:
                            logging.warning(
                                f"Could not find or click checkbox for experience level: '{exp_level}'. Skipping.")
                    except Exception as e:
                        logging.warning(f"Error selecting experience level '{exp_level}': {e}")

                # Click Apply/Done button if present
                try:
                    apply_buttons = driver.find_elements(By.XPATH,
                                                         "//button[contains(text(), 'Apply') or contains(text(), 'Done') or contains(text(), 'Show results')]")
                    if apply_buttons:
                        apply_buttons[0].click()
                        human_delay()
                        filters_applied = True
                except Exception as e:
                    logging.warning(f"Error clicking apply/done button: {e}")

                logging.info("'Experience Level' filter(s) applied.")

        except Exception as e:
            logging.error(f"Error applying 'Experience Level' filter: {e}")

    # Wait for filter results to apply
    try:
        # Wait for any loading indicator to disappear
        loading_indicators = [
            "//div[contains(@class, 'jobs-search-results-list__loader')]",
            "//div[contains(@class, 'artdeco-loader')]"
        ]

        for indicator in loading_indicators:
            try:
                # First check if it exists
                elements = driver.find_elements(By.XPATH, indicator)
                if elements:
                    # If it exists, wait for it to disappear
                    WebDriverWait(driver, 15).until(
                        EC.invisibility_of_element_located((By.XPATH, indicator))
                    )
                    break
            except:
                continue
    except Exception as e:
        logging.error(f"Error waiting for filters to apply: {e}")

    if not filters_applied:
        logging.warning("Some filters could not be applied. Check logs.")

    # Allow extra time for results to load after filter application
    human_delay(2.0, 4.0)
    return filters_applied


def scrape_jobs_on_page(driver, easy_apply_only=True):
    """Scrapes job listings from the current page."""
    logging.info("\n--- Starting Job Scraping Process (Page 1) ---")
    logging.info("Starting to scrape jobs on the current page...")
    job_data = []

    try:
        # Wait for job list container - trying multiple possible selectors
        job_list_selectors = [
            "div.scaffold-layout__list > ul",  # Original selector
            ".jobs-search-results-list",  # Alternative
            ".scaffold-layout__list",  # Detected in logs
            "div[data-view-name='job-serp-jobs-list']"  # Another possibility
        ]

        job_list_container = None
        for selector in job_list_selectors:
            try:
                job_list_container = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                break
            except TimeoutException:
                continue

        if not job_list_container:
            logging.error("Timed out waiting for the job list container.")
            return job_data

        # Find all job cards - multiple possible selectors
        job_card_selectors = [
            ".jobs-search-results__list-item",
            "li.occludable-update",
            "li.scaffold-layout__list-item",
            "div[data-job-id]"  # Some LinkedIn versions use data attributes
        ]

        job_cards = []
        for selector in job_card_selectors:
            job_cards = driver.find_elements(By.CSS_SELECTOR, selector)
            if job_cards:
                logging.info(f"Found {len(job_cards)} job listings using selector: {selector}")
                break

        if not job_cards:
            logging.warning("No job cards found on this page.")
            return job_data

        # Process each job card
        for index, job_card in enumerate(job_cards[:10]):  # Limit to first 10 for testing
            try:
                # Click on the job card to view details
                try:
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                          job_card)
                    human_delay(0.5, 1.0)

                    # Try clicking normally first
                    try:
                        job_card.click()
                    except:
                        # If direct click fails, try JavaScript click
                        driver.execute_script("arguments[0].click();", job_card)

                    human_delay(1.0, 2.0)
                except Exception as e:
                    logging.warning(f"Could not click job card {index + 1}: {e}")
                    continue

                # Wait for job details to load
                job_details_loaded = False
                details_selectors = [
                    ".jobs-unified-top-card__content-container",
                    ".jobs-details",
                    "h2.jobs-unified-top-card__job-title"
                ]

                for selector in details_selectors:
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        job_details_loaded = True
                        break
                    except:
                        continue

                if not job_details_loaded:
                    logging.warning(f"Could not load details for job {index + 1}")
                    continue

                # Check if Easy Apply button exists (if easy_apply_only is True)
                if easy_apply_only:
                    easy_apply_selectors = [
                        "button.jobs-apply-button",
                        "button[aria-label*='Easy Apply']",
                        "button span[text()='Easy Apply']",
                        ".jobs-s-apply button"
                    ]

                    has_easy_apply = False
                    for selector in easy_apply_selectors:
                        if len(driver.find_elements(By.CSS_SELECTOR, selector)) > 0:
                            has_easy_apply = True
                            break

                    if not has_easy_apply:
                        logging.info(f"Job {index + 1}: Skipping as it's not Easy Apply")
                        continue

                # Extract job details
                job_info = {}

                # Title
                try:
                    title_selectors = [
                        "h2.jobs-unified-top-card__job-title",
                        ".jobs-unified-top-card__job-title",
                        "h2.t-24"
                    ]
                    for selector in title_selectors:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            job_info["title"] = elements[0].text.strip()
                            break
                except Exception as e:
                    logging.warning(f"Could not extract job title: {e}")
                    job_info["title"] = "Unknown Title"

                # Company
                try:
                    company_selectors = [
                        ".jobs-unified-top-card__company-name",
                        "a.ember-view.t-black.t-normal",
                        "span.jobs-unified-top-card__subtitle-primary-grouping a"
                    ]
                    for selector in company_selectors:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            job_info["company"] = elements[0].text.strip()
                            break
                except Exception as e:
                    logging.warning(f"Could not extract company name: {e}")
                    job_info["company"] = "Unknown Company"

                # Location
                try:
                    location_selectors = [
                        ".jobs-unified-top-card__bullet",
                        ".jobs-unified-top-card__subtitle-primary-grouping .jobs-unified-top-card__bullet",
                        "span.jobs-unified-top-card__location"
                    ]
                    for selector in location_selectors:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            job_info["location"] = elements[0].text.strip()
                            break
                except Exception as e:
                    logging.warning(f"Could not extract location: {e}")
                    job_info["location"] = "Unknown Location"

                # Job URL - get current URL as it should be the job details page
                job_info["url"] = driver.current_url

                # Job Description - try multiple selectors
                try:
                    desc_selectors = [
                        ".jobs-description__content",
                        ".jobs-description-content",
                        ".jobs-box__html-content"
                    ]
                    for selector in desc_selectors:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            job_info["description"] = elements[0].text.strip()
                            break

                    if "description" not in job_info:
                        # If specific selectors fail, try to get all job details text
                        job_info["description"] = driver.find_element(By.CSS_SELECTOR, ".jobs-details").text
                except Exception as e:
                    logging.warning(f"Could not extract job description: {e}")
                    job_info["description"] = "Description not available"

                # Date Posted/Listed - Often appears in the job details
                try:
                    date_selectors = [
                        ".jobs-unified-top-card__subtitle-secondary-grouping .jobs-unified-top-card__posted-date",
                        ".jobs-posted-time-status",
                        "span.jobs-unified-top-card__posted-date"
                    ]
                    for selector in date_selectors:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            job_info["date_posted"] = elements[0].text.strip()
                            break
                except Exception as e:
                    logging.warning(f"Could not extract date posted: {e}")
                    job_info["date_posted"] = "Unknown"

                # Add a timestamp
                job_info["scraped_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                logging.info(
                    f"Job {index + 1}: Scraped {job_info.get('title', 'Unknown')} at {job_info.get('company', 'Unknown')}")
                job_data.append(job_info)

                human_delay(1.0, 2.0)
            except Exception as e:
                logging.error(f"Error processing job card {index + 1}: {e}")
                continue

        logging.info("\n--- Scraping Complete for First Page ---")
    except Exception as e:
        logging.error(f"Error during job scraping: {e}")

    if not job_data:
        logging.warning("No job data was collected from the first page. Check logs and selectors.")

    return job_data


def save_results(job_data, file_format="json"):
    """Saves the scraped job data to a file."""
    if not job_data:
        logging.warning("No job data to save.")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if file_format.lower() == "json":
        filename = f"linkedin_jobs_{timestamp}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Job data saved to {filename}")
            return True
        except Exception as e:
            logging.error(f"Error saving job data to JSON: {e}")
            return False
    elif file_format.lower() == "txt":
        filename = f"linkedin_jobs_{timestamp}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for job in job_data:
                    f.write(f"Title: {job.get('title', 'Unknown')}\n")
                    f.write(f"Company: {job.get('company', 'Unknown')}\n")
                    f.write(f"Location: {job.get('location', 'Unknown')}\n")
                    f.write(f"Posted: {job.get('date_posted', 'Unknown')}\n")
                    f.write(f"URL: {job.get('url', '')}\n")
                    f.write(f"Description: {job.get('description', 'No description available')[:500]}...\n")
                    f.write("\n" + "-" * 80 + "\n\n")
            logging.info(f"Job data saved to {filename}")
            return True
        except Exception as e:
            logging.error(f"Error saving job data to TXT: {e}")
            return False
    else:
        logging.error(f"Unsupported file format: {file_format}")
        return False


def main():
    """Main execution function."""
    # Get the current iteration from environment or use a default
    iteration = os.getenv("BOT_ITERATION", "3")

    logging.info(f"--- LinkedIn Bot Started (Iteration {iteration}) ---")
    logging.info(f"--- LinkedIn Bot: Iteration {iteration} - Job Scraping ---")

    # Load configuration
    config = load_config()

    # Setup WebDriver
    driver = setup_driver()
    if not driver:
        logging.critical("Failed to initialize WebDriver. Exiting.")
        return False

    try:
        # Login to LinkedIn
        if not login_with_retry(driver, LINKEDIN_EMAIL, LINKEDIN_PASSWORD):
            logging.critical("Login failed. Exiting.")
            return False

        # Navigate to Jobs page
        if not navigate_to_jobs_page(driver):
            logging.critical("Failed to navigate to Jobs page. Exiting.")
            return False

        # Wait for any onboarding dialogs to disappear
        human_delay(2.0, 4.0)

        # Perform job search
        search_criteria = config.get("search_criteria", DEFAULT_CONFIG["search_criteria"])
        if not perform_job_search(driver,
                                  search_criteria.get("keywords"),
                                  search_criteria.get("location")):
            logging.critical("Failed to perform job search. Exiting.")
            return False

        # Apply filters
        filters = config.get("filters", DEFAULT_CONFIG["filters"])
        apply_filters(driver,
                      date_posted=filters.get("date_posted"),
                      experience_levels=filters.get("experience_level"))

        # Scrape jobs on the current page
        scraping_config = config.get("scraping", DEFAULT_CONFIG["scraping"])
        job_data = scrape_jobs_on_page(driver, easy_apply_only=scraping_config.get("easy_apply_only", True))

        # Save results if requested
        output_config = config.get("output", DEFAULT_CONFIG["output"])
        if output_config.get("save_to_file", True) and job_data:
            save_results(job_data, file_format=output_config.get("file_format", "json"))

        return True
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")
        return False
    finally:
        if driver:
            logging.info("Closing WebDriver.")
            driver.quit()
        logging.info("--- Bot Execution Finished ---")


if __name__ == "__main__":
    main()
