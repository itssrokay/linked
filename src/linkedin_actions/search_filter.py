# src/linkedin_actions/search_filter.py
import logging
import time
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException

# Import helper from the utils directory
from ..utils.helpers import human_delay

# Directly copied from the provided code
def perform_job_search(driver, keywords, location):
    """Enters search keywords and location and initiates the search."""
    logging.info(f"Performing job search for Keywords: '{keywords}', Location: '{location}'")
    try:
        # Find keyword input field (using original selector)
        keyword_input_selector = "input[id*='jobs-search-box-keyword-id']"
        keyword_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, keyword_input_selector))
        )
        keyword_input.clear()
        keyword_input.send_keys(keywords)
        human_delay(0.5, 1.0) # Using helper

        # Find location input field (using original selector)
        location_input_selector = "input[id*='jobs-search-box-location-id']"
        location_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, location_input_selector))
        )
        # Clear location field thoroughly (using original method)
        location_input.send_keys(Keys.CONTROL + "a")
        location_input.send_keys(Keys.BACKSPACE)
        human_delay(0.3, 0.7) # Using helper
        location_input.send_keys(location)
        human_delay(1.0, 2.0)  # Allow time for suggestions (using helper)
        location_input.send_keys(Keys.ENTER)  # Submit search via Enter key (original method)
        logging.info("Search criteria entered. Submitted search via Enter key.")

        # --- Wait for results page to load with multiple detection strategies --- (Exact logic from original)
        logging.info("Waiting for search results page to load...")

        # Define multiple possible selectors for detecting the results page (Exact list from original)
        possible_selectors = [
            {"type": "css", "value": "div.scaffold-layout__list > ul", "name": "Job list container"},
            {"type": "css", "value": ".jobs-search-results-list", "name": "Jobs results list"},
            {"type": "css", "value": ".scaffold-layout__list", "name": "Scaffold layout list"},
            {"type": "xpath", "value": "//div[contains(@class, 'jobs-search-results')]", "name": "Jobs search results div"},
            {"type": "css", "value": ".jobs-search-no-results", "name": "No results indicator"},
            {"type": "xpath", "value": "//button[contains(text(), 'Date posted')]", "name": "Date posted filter button"},
            {"type": "xpath", "value": "//li[contains(@class, 'jobs-search-results__list-item')]", "name": "Any job list item"},
            {"type": "xpath", "value": "//div[contains(@class, 'jobs-search-results-grid')]", "name": "Jobs results grid"} # Added in original's code
        ]

        # Try each selector with a short timeout (Exact loop from original)
        for selector in possible_selectors:
            try:
                logging.info(f"Trying to locate {selector['name']}: {selector['value']}")
                if selector['type'] == 'css':
                    WebDriverWait(driver, 8).until( # Original timeout: 8s
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector['value']))
                    )
                else:
                    WebDriverWait(driver, 8).until( # Original timeout: 8s
                        EC.presence_of_element_located((By.XPATH, selector['value']))
                    )
                logging.info(f"Search results page detected using {selector['name']}!")
                human_delay() # Using helper
                return True
            except TimeoutException:
                logging.warning(f"Could not find {selector['name']} within timeout")
                continue

        # If direct selectors don't work, try a URL-based approach (Exact logic from original)
        try:
            logging.info("Trying URL-based detection...")
            WebDriverWait(driver, 10).until( # Original timeout: 10s
                lambda d: "jobs/search" in d.current_url
            )
            logging.info("Job search URL detected. Assuming results page loaded.")
            screenshot_path = f"job_search_results_{time.strftime('%Y%m%d%H%M%S')}.png"
            driver.save_screenshot(screenshot_path) # Save screenshot exactly as in original
            logging.info(f"Saved screenshot to {screenshot_path}")
            human_delay() # Using helper
            return True
        except TimeoutException:
            logging.warning("URL-based detection also failed")

        # Final fallback: check if page structure changed significantly (Exact logic from original)
        logging.info("Trying generic page change detection...")
        old_source_len = len(driver.page_source)
        human_delay(5.0, 7.0)  # Wait longer (using helper)
        new_source_len = len(driver.page_source)

        if abs(new_source_len - old_source_len) > 5000:  # Significant change threshold (original value)
            logging.info("Page content changed significantly. Assuming results loaded.")
            screenshot_path = f"generic_change_results_{time.strftime('%Y%m%d%H%M%S')}.png"
            driver.save_screenshot(screenshot_path) # Save screenshot exactly as in original
            logging.info(f"Saved screenshot to {screenshot_path}")
            return True

        # If all detection methods fail (Exact logic from original)
        logging.error("None of the detection methods could identify the search results page")
        debug_filename = f"debug_page_source_search_fail_{time.strftime('%Y%m%d%H%M%S')}.html"
        with open(debug_filename, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info(f"Saved page source to {debug_filename}")
        screenshot_path = f"failed_search_results_{time.strftime('%Y%m%d%H%M%S')}.png"
        driver.save_screenshot(screenshot_path)
        logging.info(f"Saved screenshot to {screenshot_path}")
        return False

    except Exception as e:
        logging.error(f"An unexpected error occurred during job search: {e}")
        # Try to save debug information even on exception (Exact logic from original)
        try:
            debug_filename = f"exception_search_fail_{time.strftime('%Y%m%d%H%M%S')}.html"
            with open(debug_filename, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logging.info(f"Saved exception page source to {debug_filename}")
        except:
            pass
        return False

# Directly copied from the provided code
def apply_filters(driver, date_posted=None, experience_levels=None):
    """Applies filters to the job search results."""
    logging.info("Applying filters...")
    filters_applied = False

    # Wait for page to stabilize after search (using original delay logic)
    human_delay(3.0, 5.0) # Using helper

    # ---- Apply Date Posted filter ---- (Exact logic from original)
    if date_posted:
        try:
            logging.info(f"Applying 'Date Posted' filter: {date_posted}")
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
                    date_button = WebDriverWait(driver, 5).until( # Original timeout: 5s
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except: continue

            if not date_button:
                logging.warning("Could not find Date Posted filter button. Skipping this filter.")
                driver.save_screenshot(f"date_filter_not_found_{time.strftime('%Y%m%d%H%M%S')}.png") # Original debug step
            else:
                try: date_button.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", date_button) # Original fallback

                human_delay() # Using helper
                option_found = False

                # Method 1: Standard checkbox approach (Exact logic from original)
                try:
                    option_labels = [
                        f"//label[contains(text(), '{date_posted}')]",
                        f"//span[contains(text(), '{date_posted}')]/ancestor::label",
                        f"//div[contains(text(), '{date_posted}')]/ancestor::label"
                    ]
                    for label_xpath in option_labels:
                        try:
                            option_label = WebDriverWait(driver, 5).until( # Original timeout: 5s
                                EC.element_to_be_clickable((By.XPATH, label_xpath))
                            )
                            option_label.click()
                            human_delay() # Using helper
                            option_found = True
                            break
                        except: continue
                except Exception as e: logging.warning(f"Error with standard checkbox approach: {e}")

                # Method 2: Dropdown selection (Exact logic from original)
                if not option_found:
                    try:
                        dropdown_items = driver.find_elements(By.XPATH, f"//div[contains(@role, 'menuitem')][contains(text(), '{date_posted}')]")
                        if dropdown_items:
                            dropdown_items[0].click()
                            option_found = True
                            human_delay() # Using helper
                    except Exception as e: logging.warning(f"Error with dropdown selection approach: {e}")

                # Method 3: Try buttons in a dialog (Exact logic from original)
                if not option_found:
                    try:
                        buttons = driver.find_elements(By.XPATH, f"//button[contains(text(), '{date_posted}')]")
                        if buttons:
                            buttons[0].click()
                            option_found = True
                            human_delay() # Using helper
                    except Exception as e: logging.warning(f"Error with button selection approach: {e}")

                # Close the filter dialog if needed (Exact logic from original)
                try:
                    apply_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Apply') or contains(text(), 'Done') or contains(text(), 'Show results')]")
                    if apply_buttons:
                        apply_buttons[0].click()
                        human_delay() # Using helper
                except Exception as e: logging.warning(f"Error clicking apply/done button: {e}")

                if not option_found:
                    logging.warning(f"Could not find or select '{date_posted}' option.")
                    driver.save_screenshot(f"date_option_not_found_{time.strftime('%Y%m%d%H%M%S')}.png") # Original debug step
                else:
                    filters_applied = True
        except Exception as e:
            logging.error(f"Error applying 'Date Posted' filter: {e}")

    # ---- Apply Experience Level filter ---- (Exact logic from original)
    if experience_levels and len(experience_levels) > 0:
        logging.info(f"Applying 'Experience Level' filter(s): {', '.join(experience_levels)}")
        try:
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
                    exp_button = WebDriverWait(driver, 5).until( # Original timeout: 5s
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except: continue

            if not exp_button:
                logging.warning("Could not find Experience Level filter button. Skipping this filter.")
                driver.save_screenshot(f"exp_filter_not_found_{time.strftime('%Y%m%d%H%M%S')}.png") # Original debug step
            else:
                try: exp_button.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", exp_button) # Original fallback

                human_delay() # Using helper

                for exp_level in experience_levels:
                    try:
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
                                    elements[0].click()
                                    checkbox_found = True
                                    human_delay(0.5, 1.0) # Using helper
                                    break
                            except: continue
                        if not checkbox_found: logging.warning(f"Could not find or click checkbox for experience level: '{exp_level}'. Skipping.")
                    except Exception as e: logging.warning(f"Error selecting experience level '{exp_level}': {e}")

                try:
                    apply_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Apply') or contains(text(), 'Done') or contains(text(), 'Show results')]")
                    if apply_buttons:
                        apply_buttons[0].click()
                        human_delay() # Using helper
                        filters_applied = True
                except Exception as e: logging.warning(f"Error clicking apply/done button: {e}")
                logging.info("'Experience Level' filter(s) applied.") # This log was here in original
        except Exception as e:
            logging.error(f"Error applying 'Experience Level' filter: {e}")

    # Wait for filter results to apply (Exact logic from original)
    try:
        loading_indicators = [
            "//div[contains(@class, 'jobs-search-results-list__loader')]",
            "//div[contains(@class, 'artdeco-loader')]"
        ]
        for indicator in loading_indicators:
            try:
                elements = driver.find_elements(By.XPATH, indicator)
                if elements:
                    WebDriverWait(driver, 15).until( # Original timeout: 15s
                        EC.invisibility_of_element_located((By.XPATH, indicator))
                    )
                    break
            except: continue
    except Exception as e:
        logging.error(f"Error waiting for filters to apply: {e}")

    if not filters_applied: # Checking the flag set within this function
        logging.warning("Some filters could not be applied. Check logs.") # Original log based on flag

    human_delay(2.0, 4.0) # Original final delay
    return filters_applied # Return the flag