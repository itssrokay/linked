# src/linkedin_actions/scrape.py
import logging
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException

# Import helper from the utils directory
from ..utils.helpers import human_delay

# Directly copied from the provided code
def scrape_jobs_on_page(driver, easy_apply_only=True):
    """Scrapes job listings from the current page."""
    # Note: The original code only scrapes the *first page* and has a hardcoded limit.
    # This function replicates that behavior exactly. Pagination logic was not in the provided scrape function.
    logging.info("\n--- Starting Job Scraping Process (Page 1) ---") # Original Log Message
    logging.info("Starting to scrape jobs on the current page...") # Original Log Message
    job_data = []

    try:
        # Wait for job list container - trying multiple possible selectors (Original logic)
        job_list_selectors = [
            "div.scaffold-layout__list > ul",  # Original selector
            ".jobs-search-results-list",      # Alternative from original
            ".scaffold-layout__list",          # Detected in logs (from original comments)
            "div[data-view-name='job-serp-jobs-list']" # Another possibility (from original comments)
        ]
        job_list_container = None
        for selector in job_list_selectors:
            try:
                job_list_container = WebDriverWait(driver, 15).until( # Original timeout: 15s
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                break
            except TimeoutException: continue

        if not job_list_container:
            logging.error("Timed out waiting for the job list container.")
            return job_data # Original return

        # Find all job cards - multiple possible selectors (Original logic)
        job_card_selectors = [
            ".jobs-search-results__list-item", # Original selector
            "li.occludable-update",           # Original selector
            "li.scaffold-layout__list-item", # Original selector
            "div[data-job-id]"                # Original selector
        ]
        job_cards = []
        for selector in job_card_selectors:
            job_cards = driver.find_elements(By.CSS_SELECTOR, selector)
            if job_cards:
                logging.info(f"Found {len(job_cards)} job listings using selector: {selector}") # Original log
                break

        if not job_cards:
            logging.warning("No job cards found on this page.") # Original log
            return job_data # Original return

        # Process each job card (Using original limit and logic)
        # !!! Original code had a hardcoded limit for testing: [:10] !!!
        # Keep this limit to exactly match the provided code's behavior.
        # Remove or change [:10] if you want to scrape all found cards on the page.
        for index, job_card in enumerate(job_cards[:10]):
            try:
                # Click on the job card to view details (Original logic)
                try:
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", job_card) # Original scroll
                    human_delay(0.5, 1.0) # Using helper

                    # Try clicking normally first (Original logic)
                    try: job_card.click()
                    except: driver.execute_script("arguments[0].click();", job_card) # Original JS fallback

                    human_delay(1.0, 2.0) # Using helper
                except Exception as e:
                    logging.warning(f"Could not click job card {index + 1}: {e}") # Original log
                    continue # Original skip

                # Wait for job details to load (Original logic)
                job_details_loaded = False
                details_selectors = [
                    ".jobs-unified-top-card__content-container", # Original selector
                    ".jobs-details",                             # Original selector
                    "h2.jobs-unified-top-card__job-title"       # Original selector
                ]
                for selector in details_selectors:
                    try:
                        WebDriverWait(driver, 10).until( # Original timeout: 10s
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        job_details_loaded = True
                        break
                    except: continue

                if not job_details_loaded:
                    logging.warning(f"Could not load details for job {index + 1}") # Original log
                    continue # Original skip

                # Check if Easy Apply button exists (if easy_apply_only is True) (Original logic)
                if easy_apply_only:
                    easy_apply_selectors = [
                        "button.jobs-apply-button",         # Original selector
                        "button[aria-label*='Easy Apply']", # Original selector
                        "button span[text()='Easy Apply']", # Original selector typo? (text() is XPath), keeping as is. Should be: //button[.//span[text()='Easy Apply']] or similar
                        ".jobs-s-apply button"              # Original selector
                    ]
                    has_easy_apply = False
                    for selector in easy_apply_selectors:
                        # Need to handle XPath vs CSS selectors based on the string
                        elements = []
                        try:
                           if selector.startswith("//") or selector.startswith("(//"):
                               elements = driver.find_elements(By.XPATH, selector)
                           else:
                               elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        except Exception as find_ex:
                             logging.debug(f"Error finding easy apply with selector {selector}: {find_ex}")

                        if len(elements) > 0:
                            has_easy_apply = True
                            break

                    if not has_easy_apply:
                        logging.info(f"Job {index + 1}: Skipping as it's not Easy Apply") # Original log
                        continue # Original skip

                # Extract job details (Original logic and selectors)
                job_info = {}

                # Title
                try:
                    title_selectors = [
                        "h2.jobs-unified-top-card__job-title", # Original selector
                        ".jobs-unified-top-card__job-title",   # Original selector
                        "h2.t-24"                              # Original selector
                    ]
                    for selector in title_selectors:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            job_info["title"] = elements[0].text.strip()
                            break
                    # Check if title was found, add default if not (added for safety, original didn't explicitly handle missing title)
                    if "title" not in job_info:
                        job_info["title"] = "Unknown Title"
                except Exception as e:
                    logging.warning(f"Could not extract job title: {e}") # Original log
                    job_info["title"] = "Unknown Title" # Original assignment in except block

                # Company
                try:
                    company_selectors = [
                        ".jobs-unified-top-card__company-name",             # Original selector
                        "a.ember-view.t-black.t-normal",                    # Original selector (Potentially fragile Ember class)
                        "span.jobs-unified-top-card__subtitle-primary-grouping a" # Original selector
                    ]
                    for selector in company_selectors:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                             # Check for empty text which sometimes happens
                             text = elements[0].text.strip()
                             if text:
                                 job_info["company"] = text
                                 break
                    if "company" not in job_info: job_info["company"] = "Unknown Company" # Added default if loop completes without finding
                except Exception as e:
                    logging.warning(f"Could not extract company name: {e}") # Original log
                    job_info["company"] = "Unknown Company" # Original assignment in except

                # Location
                try:
                    location_selectors = [
                        ".jobs-unified-top-card__bullet",                                # Original selector
                        ".jobs-unified-top-card__subtitle-primary-grouping .jobs-unified-top-card__bullet", # Original selector
                        "span.jobs-unified-top-card__location"                          # Original selector
                    ]
                    for selector in location_selectors:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            text = elements[0].text.strip()
                            if text: # Check if text is not empty
                                job_info["location"] = text
                                break
                    if "location" not in job_info: job_info["location"] = "Unknown Location" # Added default
                except Exception as e:
                    logging.warning(f"Could not extract location: {e}") # Original log
                    job_info["location"] = "Unknown Location" # Original assignment in except

                # Job URL - get current URL as it should be the job details page (Original logic)
                job_info["url"] = driver.current_url

                # Job Description - try multiple selectors (Original logic)
                try:
                    desc_selectors = [
                        ".jobs-description__content", # Original selector
                        ".jobs-description-content", # Original selector
                        ".jobs-box__html-content"    # Original selector
                    ]
                    desc_found = False
                    for selector in desc_selectors:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            job_info["description"] = elements[0].text.strip()
                            desc_found = True
                            break

                    if not desc_found: # Original fallback logic
                        # If specific selectors fail, try to get all job details text
                        job_info["description"] = driver.find_element(By.CSS_SELECTOR, ".jobs-details").text # Original fallback selector
                except Exception as e:
                    logging.warning(f"Could not extract job description: {e}") # Original log
                    job_info["description"] = "Description not available" # Original assignment in except

                # Date Posted/Listed - Often appears in the job details (Original logic)
                try:
                    date_selectors = [
                        ".jobs-unified-top-card__subtitle-secondary-grouping .jobs-unified-top-card__posted-date", # Original selector
                        ".jobs-posted-time-status", # Original selector
                        "span.jobs-unified-top-card__posted-date" # Original selector
                    ]
                    date_found = False
                    for selector in date_selectors:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            job_info["date_posted"] = elements[0].text.strip()
                            date_found = True
                            break
                    if not date_found: job_info["date_posted"] = "Unknown" # Default if not found
                except Exception as e:
                    logging.warning(f"Could not extract date posted: {e}") # Original log
                    job_info["date_posted"] = "Unknown" # Original assignment in except

                # Add a timestamp (Original logic)
                job_info["scraped_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Original format

                logging.info(f"Job {index + 1}: Scraped {job_info.get('title', 'Unknown')} at {job_info.get('company', 'Unknown')}") # Original log
                job_data.append(job_info)

                human_delay(1.0, 2.0) # Using helper, original position
            except Exception as e:
                logging.error(f"Error processing job card {index + 1}: {e}") # Original log
                continue # Original skip

        logging.info("\n--- Scraping Complete for First Page ---") # Original log
    except Exception as e:
        logging.error(f"Error during job scraping: {e}") # Original log

    if not job_data:
        logging.warning("No job data was collected from the first page. Check logs and selectors.") # Original log

    return job_data # Original return