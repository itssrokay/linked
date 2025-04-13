# src/linkedin_actions/login.py
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import helper from the utils directory
from ..utils.helpers import human_delay

# Define URL here or pass as argument, keeping it local for now
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"

# Directly copied from the provided code
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
            input("Press Enter after completing the verification manually...") # Exactly as in original code
            if "feed" in driver.current_url:
                logging.info("Verification successful! Now on feed.")
                return True
            return False
        elif "/login" in current_url:
            try:
                error_msg = driver.find_element(By.ID, "error-for-password") # Using ID from original code
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
            # Original code didn't explicitly return True/False here, but implicitly assumed success if not login/checkpoint
            # Let's return True to match the implied behavior of continuing the script.
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

# Directly copied from the provided code
def login_with_retry(driver, email, password, max_attempts=2):
    """Attempt to login multiple times in case of transient failures."""
    for attempt in range(1, max_attempts + 1):
        logging.info(f"Login attempt {attempt}/{max_attempts}")
        # Calls the single attempt function defined above
        if login_to_linkedin(driver, email, password):
            logging.info("\nLogin successful. Proceeding...\n") # Added newline as in original
            return True

        if attempt < max_attempts:
            wait_time = 5 * attempt  # Progressive backoff
            logging.info(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)

            # If we were redirected to an unexpected page, go back to login
            if "/login" not in driver.current_url:
                logging.info("Navigating back to login page for retry...")
                # Use the constant defined at the top of this file
                driver.get(LINKEDIN_LOGIN_URL)
                time.sleep(2) # Using sleep from original logic

    logging.error(f"Failed to login after {max_attempts} attempts.")
    return False