# src/linkedin_actions/login.py
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Assuming helpers are in ../utils relative to this file's location
from ..utils.helpers import human_delay

LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"

def _login_attempt(driver, email, password):
    """Performs a single login attempt."""
    if not driver:
        logging.error("WebDriver not initialized.")
        return False, "WebDriver not initialized."

    logging.info(f"Navigating to LinkedIn login page: {LINKEDIN_LOGIN_URL}")
    try:
        driver.get(LINKEDIN_LOGIN_URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        logging.info("Login page loaded.")
    except TimeoutException:
        logging.error("Timed out waiting for the LinkedIn login page to load.")
        return False, "Login page timeout"
    except Exception as e:
        logging.error(f"Error navigating to login page: {e}")
        return False, f"Navigation error: {e}"

    try:
        logging.info("Attempting to fill login credentials...")
        # Find username/email field and enter email
        username_field = driver.find_element(By.ID, "username")
        username_field.clear()
        username_field.send_keys(email)
        human_delay(0.6, 1.2)

        # Find password field and enter password
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(password)
        human_delay(0.6, 1.2)

        # Find and click the login button
        # Using a more robust XPath that works even if text changes slightly
        login_button_xpath = "//button[contains(@aria-label, 'Sign in') or @type='submit']"
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, login_button_xpath))
        )
        login_button.click()
        logging.info("Login button clicked.")
        logging.info("Waiting for page transition after login click...")

        # Wait for redirection indicating success, failure, or checkpoint
        # Increased wait time as network/LinkedIn can be slow
        WebDriverWait(driver, 30).until(
            lambda d: "feed" in d.current_url or # Success
                      "checkpoint" in d.current_url or # Security check
                      "challenge" in d.current_url or # Another type of check
                      "/login" not in d.current_url or # Maybe redirected somewhere else valid?
                      d.find_elements(By.ID, "error-for-password") # Error message appeared
        )

        current_url = driver.current_url
        logging.info(f"URL after login attempt: {current_url}")

        # Check results
        if "feed" in current_url:
            logging.info("Login Successful! Redirected to the feed.")
            return True, "Login successful"
        elif "checkpoint" in current_url or "challenge" in current_url:
            logging.warning("Login Alert: LinkedIn security check required (CAPTCHA, verification, etc.).")
            # You might need manual intervention here
            # Add a prompt for manual completion
            print("\n" + "*"*60)
            print("ACTION REQUIRED: Please complete the security verification")
            print("in the automated browser window.")
            print("*"*60 + "\n")
            input("Press Enter here in the console AFTER completing the verification...")
            # Re-check URL after manual step
            if "feed" in driver.current_url:
                 logging.info("Manual verification successful. Proceeding.")
                 return True, "Manual verification successful"
            else:
                 logging.error("Manual verification may have failed or timed out.")
                 return False, "Manual verification failed"

        elif "/login" in current_url:
            try:
                error_msg_element = driver.find_element(By.CSS_SELECTOR, ".form__label--error") # Check common error class
                if error_msg_element and error_msg_element.is_displayed():
                    error_text = error_msg_element.text.strip()
                    logging.error(f"Login Failed: {error_text}")
                    return False, f"Login failed: {error_text}"
                # Check for password specific error
                error_msg_element = driver.find_element(By.ID, "error-for-password")
                if error_msg_element and error_msg_element.is_displayed():
                    error_text = error_msg_element.text.strip()
                    logging.error(f"Login Failed: {error_text}")
                    return False, f"Login failed: {error_text}"

            except NoSuchElementException:
                logging.error("Login Failed: Still on login page, but no specific error message found. Check credentials.")
                return False, "Login failed (no error message)"
            except Exception as e:
                 logging.error(f"Login Failed: Error checking for failure messages: {e}")
                 return False, f"Login failed (error check exception: {e})"
        else:
            # Successfully logged in but redirected somewhere unexpected? Treat as success for now.
            logging.warning(f"Login Status Uncertain: Redirected to {current_url}. Assuming success.")
            return True, "Login successful (unexpected redirect)"

    except TimeoutException as e:
        logging.error(f"Login Error: Timed out waiting for an element. {e}")
        return False, "Login timeout"
    except NoSuchElementException as e:
        logging.error(f"Login Error: Could not find an element (username, password, or login button). UI Change? {e}")
        return False, "Login element not found"
    except Exception as e:
        logging.error(f"An unexpected error occurred during login attempt: {e}")
        return False, f"Unexpected login error: {e}"

def login_with_retry(driver, email, password, max_attempts=2):
    """Attempts to login multiple times."""
    for attempt in range(1, max_attempts + 1):
        logging.info(f"Login attempt {attempt}/{max_attempts}")
        success, message = _login_attempt(driver, email, password)
        if success:
            return True

        logging.warning(f"Login attempt {attempt} failed: {message}")

        if attempt < max_attempts and "verification" not in message.lower(): # Don't retry immediately after manual step failure
            wait_time = 5 * attempt # Progressive backoff
            logging.info(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
            # If somehow not on login page, navigate back
            if "/login" not in driver.current_url and "checkpoint" not in driver.current_url and "challenge" not in driver.current_url:
                 logging.info("Navigating back to login page for retry...")
                 try:
                     driver.get(LINKEDIN_LOGIN_URL)
                     human_delay(2, 3)
                 except Exception as e:
                     logging.error(f"Failed to navigate back to login page: {e}")
                     # Might be fatal, stop retrying
                     break
        elif "verification" in message.lower():
            logging.error("Stopping login attempts after failed manual verification.")
            break # Don't retry if manual step failed


    logging.error(f"Failed to login after {max_attempts} attempts.")
    return False