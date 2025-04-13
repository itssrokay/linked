# src/linkedin_actions/scrape.py
import logging
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

from ..utils.helpers import human_delay, human_like_scroll

def _get_element_text(driver, selectors, default="Unknown"):
    """Safely extracts text from the first matching selector."""
    for selector_type, selector_value in selectors:
        try:
            element = driver.find_element(selector_type, selector_value)
            # Wait slightly for text to potentially populate if element was just rendered
            # time.sleep(0.1)
            text = element.text.strip()
            if text:
                return text
        except (NoSuchElementException, StaleElementReferenceException):
            continue
        except Exception as e:
            logging.warning(f"Error extracting text with {selector_type}={selector_value}: {e}")
            continue
    return default

def scrape_jobs_on_page(driver, easy_apply_only=True):
    """Scrapes job listings from the currently visible results page."""
    logging.info("--- Starting Job Scraping on Current Page ---")
    job_data = []
    processed_job_ids = set() # Keep track of jobs already processed on this page

    try:
        # Wait for the job list container to be present
        job_list_container_selector = ".jobs-search-results-list, .scaffold-layout__list ul"
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, job_list_container_selector))
        )

        # --- Find Job Cards ---
        # LinkedIn lazy-loads jobs as you scroll. Scroll down first to load more.
        logging.info("Scrolling down to load job listings...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 5 # Limit scrolling attempts
        while scroll_attempts < max_scroll_attempts:
             # Scroll down a bit more than window height
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            human_delay(1.5, 2.5) # Wait for jobs to load
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                 logging.info("Reached bottom of page or no more jobs loaded.")
                 break
            last_height = new_height
            scroll_attempts += 1
        logging.info("Finished scrolling.")
        human_delay(1,2) # Settle

        # Get all job cards currently loaded
        job_card_selectors = [
            "li.jobs-search-results__list-item", # Common list item structure
            "li.occludable-update",             # Another observed structure
            "div.job-search-card"               # Card-based structure
        ]
        job_cards = []
        for selector in job_card_selectors:
            job_cards = driver.find_elements(By.CSS_SELECTOR, selector)
            if job_cards:
                logging.info(f"Found {len(job_cards)} potential job listings using selector: {selector}")
                break

        if not job_cards:
            logging.warning("No job cards found on this page after scrolling.")
            # Check for "No results" message
            try:
                no_results = driver.find_element(By.CSS_SELECTOR, ".jobs-search-no-results")
                if no_results:
                    logging.info("Found 'No results' message on page.")
            except NoSuchElementException:
                pass # No results message not found, maybe just an empty list
            return job_data

        # --- Process Each Job Card ---
        job_details_pane_selector = ".jobs-search__job-details--container, .jobs-details-pane" # Right-hand details pane

        for index, job_card in enumerate(job_cards):
            job_info = {}
            try:
                # Get a unique identifier for the job if possible (data-job-id or link href)
                job_id = job_card.get_attribute("data-entity-urn") or job_card.get_attribute("data-job-id")
                if not job_id:
                     try:
                          link_element = job_card.find_element(By.TAG_NAME, "a")
                          job_id = link_element.get_attribute("href")
                     except:
                          job_id = f"card_{index}" # Fallback ID

                if job_id in processed_job_ids:
                    logging.debug(f"Skipping already processed job ID: {job_id}")
                    continue

                # Scroll the card into view for interaction
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", job_card)
                human_delay(0.6, 1.2)

                # Click the job card to load details in the right pane
                try:
                    job_card.click()
                except ElementClickInterceptedException:
                    logging.warning(f"Job card {index+1} click intercepted, trying JS click.")
                    driver.execute_script("arguments[0].click();", job_card)
                except StaleElementReferenceException:
                    logging.warning(f"Job card {index+1} became stale before clicking. Skipping.")
                    continue
                except Exception as click_err:
                     logging.warning(f"Could not click job card {index + 1}: {click_err}")
                     continue

                human_delay(1.5, 3.0) # Wait for details pane to update

                # Wait for the details pane to show some content (e.g., job title)
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, f"{job_details_pane_selector} h2"))
                    )
                except TimeoutException:
                    logging.warning(f"Timed out waiting for details pane to update for job {index + 1}. Skipping.")
                    processed_job_ids.add(job_id) # Mark as processed even if failed
                    continue

                # Check for Easy Apply button (if required)
                easy_apply_present = False
                if easy_apply_only:
                    easy_apply_selectors = [
                        (By.CSS_SELECTOR, "button.jobs-apply-button[data-job-id]"), # Standard Easy Apply
                        (By.CSS_SELECTOR, "button.jobs-s-apply__button"),            # Another variant
                        (By.XPATH, "//button[.//span[text()='Easy Apply']]"),     # Button containing 'Easy Apply' span
                        (By.CSS_SELECTOR, ".jobs-apply-button--top-card")          # Top card apply button
                    ]
                    for selector_type, selector_value in easy_apply_selectors:
                        try:
                            if driver.find_elements(selector_type, selector_value):
                                easy_apply_present = True
                                break
                        except StaleElementReferenceException: # Can happen if pane reloads
                             human_delay(0.5,1.0)
                             if driver.find_elements(selector_type, selector_value):
                                easy_apply_present = True
                                break
                        except: # Ignore other errors for this check
                             pass

                    if not easy_apply_present:
                        logging.info(f"Job {index + 1}: Skipping as 'Easy Apply' button not found (or easy_apply_only=True).")
                        processed_job_ids.add(job_id) # Mark as processed
                        continue
                # Note: Even if not easy_apply_only, we store if it was found
                job_info["easy_apply"] = easy_apply_present


                # --- Extract Details from Right Pane ---
                # Define selectors for each piece of information
                title_selectors = [
                    (By.CSS_SELECTOR, f"{job_details_pane_selector} h2"),
                    (By.CSS_SELECTOR, ".jobs-unified-top-card__job-title"),
                    (By.CSS_SELECTOR, ".t-24.t-bold") # More generic title class
                ]
                company_selectors = [
                    (By.CSS_SELECTOR, f"{job_details_pane_selector} .jobs-unified-top-card__company-name a"),
                    (By.CSS_SELECTOR, f"{job_details_pane_selector} span.jobs-unified-top-card__company-name"), # Sometimes not a link
                    (By.XPATH, f"//div[contains(@class, 'job-details')]//a[contains(@href, '/company/')]"),
                    (By.CSS_SELECTOR, ".job-card-container__company-name") # From card if pane fails?
                ]
                location_selectors = [
                    (By.CSS_SELECTOR, f"{job_details_pane_selector} .jobs-unified-top-card__location"),
                    (By.CSS_SELECTOR, f"{job_details_pane_selector} span.t-black--light.t-14"), # Generic location class?
                ]
                date_selectors = [
                    (By.CSS_SELECTOR, f"{job_details_pane_selector} .jobs-unified-top-card__posted-date"),
                    (By.CSS_SELECTOR, f"{job_details_pane_selector} span.jobs-jymbii__list-item--bullet"), # Often near date
                    (By.CSS_SELECTOR, "span.jobs-unified-top-card__subtitle-secondary-grouping") # Container often has date
                ]
                description_selectors = [
                    (By.CSS_SELECTOR, "#job-details,.jobs-description-content__text"), # Primary description areas
                    (By.CSS_SELECTOR, ".jobs-description"),
                    (By.CSS_SELECTOR, ".jobs-box__html-content")
                ]

                # Extract using the helper function
                job_info["title"] = _get_element_text(driver, title_selectors, "Unknown Title")
                job_info["company"] = _get_element_text(driver, company_selectors, "Unknown Company")
                job_info["location"] = _get_element_text(driver, location_selectors, "Unknown Location")
                job_info["date_posted"] = _get_element_text(driver, date_selectors, "Unknown Date") # May need parsing
                job_info["description"] = _get_element_text(driver, description_selectors, "Description not available")

                # Get the specific job URL from the link in the card (often more stable)
                try:
                     link_element = job_card.find_element(By.CSS_SELECTOR, "a.job-card-list__title, a.job-card-container__link")
                     job_info["url"] = link_element.get_attribute("href").split('?')[0] # Clean URL
                except:
                     job_info["url"] = driver.current_url # Fallback to current URL

                job_info["scraped_at"] = datetime.now().isoformat()

                logging.info(f"Job {index + 1}/{len(job_cards)}: Scraped '{job_info['title']}' at '{job_info['company']}' (Easy Apply: {job_info['easy_apply']})")
                job_data.append(job_info)
                processed_job_ids.add(job_id) # Mark as successfully processed

                human_delay(0.8, 1.5) # Pause before next job

            except StaleElementReferenceException:
                logging.warning(f"StaleElementReferenceException encountered processing job card {index + 1}. Skipping.")
                # Don't add job_id to processed if stale before basic info grab
                human_delay(0.5, 1.0) # Small pause before retrying loop
                continue # Move to the next card
            except Exception as e:
                logging.error(f"Error processing job card {index + 1}: {e}", exc_info=False) # Don't need full traceback always
                 # Mark as processed to avoid retrying problematic card
                if 'job_id' in locals() and job_id:
                    processed_job_ids.add(job_id)
                continue

        logging.info(f"\n--- Scraping Complete for this Page ---")
        logging.info(f"Successfully scraped {len(job_data)} jobs from this page.")

    except Exception as e:
        logging.error(f"A critical error occurred during the scraping process on this page: {e}", exc_info=True)
        driver.save_screenshot(f"debug_scrape_critical_error_{time.strftime('%Y%m%d%H%M%S')}.png")

    return job_data