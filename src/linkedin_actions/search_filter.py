# src/linkedin_actions/search_filter.py
import logging
import time
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException

from ..utils.helpers import human_delay

def perform_job_search(driver, keywords, location):
    """Enters search keywords and location and initiates the search."""
    logging.info(f"Performing job search for Keywords: '{keywords}', Location: '{location}'")
    try:
        # Find keyword input field using a more robust selector
        keyword_input_selector = "input[aria-label*='Search by title, skill, or company' i], input[id*='keyword']"
        keyword_input = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, keyword_input_selector))
        )
        keyword_input.clear()
        keyword_input.send_keys(keywords)
        human_delay(0.5, 1.0)

        # Find location input field
        location_input_selector = "input[aria-label*='location' i], input[id*='location']"
        location_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, location_input_selector))
        )
        # Clear location field thoroughly - multiple backspaces might be needed
        current_location = location_input.get_attribute('value')
        for _ in range(len(current_location) + 5): # Add buffer
            location_input.send_keys(Keys.BACKSPACE)
        human_delay(0.3, 0.7)
        location_input.send_keys(location)
        human_delay(1.5, 2.5) # Allow time for location suggestions to appear and potentially select

        # Click the main search button OR press Enter in location field
        try:
            search_button_selector = "button[data-searchbar-type='JOBS'], button[aria-label*='Search jobs' i]"
            search_button = WebDriverWait(driver, 5).until(
                 EC.element_to_be_clickable((By.CSS_SELECTOR, search_button_selector))
            )
            search_button.click()
            logging.info("Clicked dedicated search button.")
        except (TimeoutException, NoSuchElementException):
            logging.warning("Dedicated search button not found or clickable, trying Enter key in location field.")
            location_input.send_keys(Keys.ENTER)
            logging.info("Submitted search via Enter key.")

        # --- Wait for results page to load ---
        logging.info("Waiting for search results page to load...")
        # Wait for the presence of the job list or the "no results" message
        results_loaded_selector = ".jobs-search-results-list, .jobs-search-no-results, .scaffold-layout__list ul"
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, results_loaded_selector))
        )
        human_delay() # Allow elements to fully render
        logging.info("Search results page appears to be loaded.")
        return True

    except TimeoutException:
        logging.error("Timed out waiting for search input fields or results list.")
        driver.save_screenshot(f"debug_search_timeout_{time.strftime('%Y%m%d%H%M%S')}.png")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during job search: {e}")
        try:
            driver.save_screenshot(f"debug_search_exception_{time.strftime('%Y%m%d%H%M%S')}.png")
        except: pass
        return False


def _click_filter_button(driver, button_text):
    """Helper to find and click a main filter button."""
    logging.debug(f"Attempting to click filter button: {button_text}")
    button_selectors = [
        f"//button[contains(., '{button_text}')]",
        f"//button[contains(@aria-label, '{button_text}')]",
        f"//button[contains(@id, '{button_text.lower().replace(' ', '-')}')]", # Guess ID
        f"//div[text()='{button_text}']//ancestor::button", # Text within div
        f"//span[text()='{button_text}']//ancestor::button" # Text within span
    ]

    for selector in button_selectors:
        try:
            button = WebDriverWait(driver, 7).until(
                EC.element_to_be_clickable((By.XPATH, selector))
            )
            # Scroll into view if needed
            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", button)
            human_delay(0.3, 0.6)
            button.click()
            logging.debug(f"Clicked filter button '{button_text}' using XPath: {selector}")
            human_delay(0.8, 1.5) # Wait for dropdown/modal
            return True
        except ElementClickInterceptedException:
            logging.warning(f"ElementClickInterceptedException for '{button_text}', trying JS click.")
            try:
                driver.execute_script("arguments[0].click();", button)
                logging.debug(f"Clicked filter button '{button_text}' using JS click.")
                human_delay(0.8, 1.5)
                return True
            except Exception as js_e:
                logging.warning(f"JS click also failed for '{button_text}': {js_e}")
                continue # Try next selector
        except (TimeoutException, NoSuchElementException):
            # logging.debug(f"Selector failed for '{button_text}': {selector}")
            continue # Try next selector

    logging.warning(f"Could not find or click filter button: '{button_text}'")
    driver.save_screenshot(f"debug_{button_text.replace(' ','_')}_filter_button_fail_{time.strftime('%Y%m%d%H%M%S')}.png")
    return False


def _select_filter_option(driver, option_text):
    """Helper to select an option within an open filter dropdown/modal."""
    logging.debug(f"Attempting to select filter option: {option_text}")
    option_selectors = [
        f"//label[normalize-space()='{option_text}']", # Exact match label
        f"//label[contains(., '{option_text}')]", # Contains text label
        f"//span[normalize-space()='{option_text}']/ancestor::label", # Text in span inside label
        f"//div[normalize-space()='{option_text}']/ancestor::label", # Text in div inside label
        f"//input[@type='radio' or @type='checkbox'][following-sibling::label[contains(., '{option_text}')]]", # Input linked to label
        f"//input[@type='radio' or @type='checkbox'][@value='{option_text}']", # Match by value attribute (less common)
        f"//div[contains(@role, 'menuitem')][contains(., '{option_text}')]", # Dropdown item
        f"//button[contains(., '{option_text}')]", # Sometimes options are buttons
    ]

    for selector in option_selectors:
        try:
            # Use find_elements to avoid immediate failure
            elements = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.XPATH, selector))
            )
            if elements:
                option_element = elements[0] # Take the first match
                # Scroll element into view
                driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", option_element)
                human_delay(0.3, 0.6)

                # Try clicking
                try:
                    option_element.click()
                except ElementClickInterceptedException:
                     driver.execute_script("arguments[0].click();", option_element) # JS fallback

                logging.debug(f"Selected filter option '{option_text}' using XPath: {selector}")
                human_delay(0.5, 1.0)
                return True
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
            # logging.debug(f"Selector failed for option '{option_text}': {selector}")
            continue # Try next selector
        except Exception as e:
            logging.warning(f"Unexpected error selecting option '{option_text}' with selector {selector}: {e}")
            continue

    logging.warning(f"Could not find or select filter option: '{option_text}'")
    # driver.save_screenshot(f"debug_{option_text.replace(' ','_')}_option_fail_{time.strftime('%Y%m%d%H%M%S')}.png")
    return False

def _apply_filter_changes(driver):
    """Helper to click the 'Apply' or 'Show results' button."""
    logging.debug("Attempting to apply filter changes...")
    apply_button_selectors = [
        "//button[contains(., 'Apply')]",
        "//button[contains(., 'Show results')]",
        "//button[contains(., 'Done')]",
        "//button[@data-control-name='filter_show_results']" # Specific attribute
    ]
    for selector in apply_button_selectors:
        try:
            apply_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, selector))
            )
            apply_button.click()
            logging.debug(f"Clicked Apply/Show results button using XPath: {selector}")
            human_delay(1.5, 3.0) # Wait for results to reload
             # Wait for potential loading indicator to disappear
            _wait_for_filter_loading(driver)
            return True
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
            continue

    logging.warning("Could not find or click Apply/Show results button. Filters might apply automatically or UI changed.")
    # Assume filters might have applied anyway if button isn't found
    human_delay(2.0, 4.0) # Extra wait just in case
    return False # Indicate button wasn't explicitly clicked

def _wait_for_filter_loading(driver, timeout=15):
    """Waits for common loading indicators to disappear after applying filters."""
    logging.debug("Waiting for filter loading indicators to disappear...")
    loading_indicators = [
        "//div[contains(@class, 'jobs-search-results-list__loader')]",
        "//div[contains(@class, 'artdeco-loader')]",
        "//div[@aria-busy='true']" # Generic busy indicator
    ]
    start_time = time.time()
    while time.time() - start_time < timeout:
        found_loader = False
        for indicator_xpath in loading_indicators:
            try:
                elements = driver.find_elements(By.XPATH, indicator_xpath)
                if elements and elements[0].is_displayed():
                    logging.debug(f"Found active loading indicator: {indicator_xpath}")
                    found_loader = True
                    break # Check this loader again
            except (NoSuchElementException, StaleElementReferenceException):
                 continue # Element might have disappeared, check others
            except Exception as e:
                 logging.warning(f"Error checking loader {indicator_xpath}: {e}")
                 continue

        if not found_loader:
            logging.debug("No active loading indicators found.")
            return True # Assume loading finished

        time.sleep(0.5) # Wait before re-checking

    logging.warning(f"Timed out waiting for loading indicators to disappear after {timeout}s.")
    return False


def apply_filters(driver, date_posted=None, experience_levels=None):
    """Applies specified filters to the job search results."""
    logging.info("Applying filters...")
    any_filter_applied = False

    # Wait briefly for filter buttons to be stable
    human_delay(2.0, 4.0)

    # Apply Date Posted filter
    if date_posted:
        logging.info(f"Applying 'Date Posted' filter: {date_posted}")
        if _click_filter_button(driver, "Date posted"):
            if _select_filter_option(driver, date_posted):
                _apply_filter_changes(driver)
                any_filter_applied = True
            else:
                logging.warning(f"Failed to select Date Posted option: {date_posted}")
                # Try to close the dropdown if stuck
                try: driver.find_element(By.TAG_NAME, 'body').click() # Click away
                except: pass
        else:
             logging.warning("Failed to open Date Posted filter.")

    # Apply Experience Level filter
    if experience_levels and isinstance(experience_levels, list) and len(experience_levels) > 0:
        logging.info(f"Applying 'Experience Level' filter(s): {', '.join(experience_levels)}")
        if _click_filter_button(driver, "Experience level"):
            options_selected_count = 0
            for level in experience_levels:
                if _select_filter_option(driver, level):
                    options_selected_count += 1
            if options_selected_count > 0:
                 _apply_filter_changes(driver)
                 any_filter_applied = True
                 if options_selected_count < len(experience_levels):
                      logging.warning("Applied some but not all specified experience levels.")
            else:
                 logging.warning(f"Failed to select any specified Experience Level options.")
                 # Try to close the dropdown if stuck
                 try: driver.find_element(By.TAG_NAME, 'body').click() # Click away
                 except: pass
        else:
             logging.warning("Failed to open Experience Level filter.")


    if any_filter_applied:
         logging.info("Filter application process finished. Waiting for results update.")
         human_delay(2.0, 4.0) # Final wait for content refresh
    else:
         logging.warning("No filters were successfully applied.")

    return any_filter_applied