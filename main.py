# main.py
import os
import logging
from dotenv import load_dotenv

# Setup logging first using the new utility
from src.utils.logger_setup import setup_logging
setup_logging()

# Import necessary functions from the refactored modules
from src.config_loader import load_config, DEFAULT_CONFIG # Import DEFAULT_CONFIG too
from src.driver_setup import setup_driver
from src.linkedin_actions.login import login_with_retry
from src.linkedin_actions.navigation import navigate_to_jobs_page
from src.linkedin_actions.search_filter import perform_job_search, apply_filters
from src.linkedin_actions.scrape import scrape_jobs_on_page
from src.output_handler import save_results
from src.utils.helpers import human_delay # Import human_delay needed for main logic pause

# --- Define Constants Used in Original Main ---
# Define paths relative to this main.py file
# CONFIG_FILE_PATH = "config/config.json"
# ENV_FILE_PATH = "config/.env" # Path to the .env file inside the config folder
project_root = os.path.dirname(__file__)
CONFIG_FILE_PATH = os.path.join(project_root, "config", "config.json")
ENV_FILE_PATH = os.path.join(project_root, "config", ".env")
# --- Main Function (Copied and adapted from original) ---
def main():
    """Main execution function."""
    # Get the current iteration from environment or use a default (original logic)
    iteration = os.getenv("BOT_ITERATION", "3") # Defaulting to 3 as in original

    logging.info(f"--- LinkedIn Bot Started (Iteration {iteration}) ---") # Original log
    # This specific log message was slightly different in the original main block, using it here:
    logging.info(f"--- LinkedIn Bot: Iteration {iteration} - Job Scraping ---") # Original specific log

    # Load environment variables (Credentials) using the specific path
    dotenv_path = os.path.join(os.path.dirname(__file__), ENV_FILE_PATH)
    if os.path.exists(dotenv_path):
         load_dotenv(dotenv_path=dotenv_path)
         logging.info(f"Loaded environment variables from: {dotenv_path}")
    else:
         logging.warning(f"Environment file not found at: {dotenv_path}. Attempting to load from default location.")
         load_dotenv() # Try loading from CWD or standard locations if not found in config/

    LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
    LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

    # Check if credentials loaded (added for safety, good practice)
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        logging.critical(f"CRITICAL: Ensure LINKEDIN_EMAIL and LINKEDIN_PASSWORD are set in {ENV_FILE_PATH} or environment.")
        return False

    # Load configuration (original call)
    config = load_config(CONFIG_FILE_PATH) # Pass the path relative to main.py

    # Setup WebDriver (original call)
    driver = setup_driver()
    if not driver:
        logging.critical("Failed to initialize WebDriver. Exiting.") # Original log
        return False

    # Use a flag or variable to track overall success if needed later
    bot_success = False

    try:
        # Login to LinkedIn (original call)
        if not login_with_retry(driver, LINKEDIN_EMAIL, LINKEDIN_PASSWORD):
            logging.critical("Login failed. Exiting.") # Original log
            # No return here in original, but added finally block ensures driver quit
            # Explicitly return False to stop script if login fails.
            return False

        # Navigate to Jobs page (original call)
        if not navigate_to_jobs_page(driver):
            logging.critical("Failed to navigate to Jobs page. Exiting.") # Original log
            return False # Stop if navigation fails

        # Wait for any onboarding dialogs to disappear (original explicit delay)
        human_delay(2.0, 4.0) # Using helper

        # Perform job search (original call, uses DEFAULT_CONFIG if keys missing)
        search_criteria = config.get("search_criteria", DEFAULT_CONFIG["search_criteria"])
        if not perform_job_search(driver,
                                  search_criteria.get("keywords"),
                                  search_criteria.get("location")):
            logging.critical("Failed to perform job search. Exiting.") # Original log
            return False # Stop if search fails

        # Apply filters (original call, uses DEFAULT_CONFIG if keys missing)
        filters = config.get("filters", DEFAULT_CONFIG["filters"])
        apply_filters(driver,
                      date_posted=filters.get("date_posted"),
                      experience_levels=filters.get("experience_level"))

        # Scrape jobs on the current page (original call)
        # Note: Original scrape function only handled one page.
        scraping_config = config.get("scraping", DEFAULT_CONFIG["scraping"])
        job_data = scrape_jobs_on_page(driver, easy_apply_only=scraping_config.get("easy_apply_only", True))

        # Save results if requested (original logic)
        output_config = config.get("output", DEFAULT_CONFIG["output"])
        if output_config.get("save_to_file", True) and job_data:
            # Using the save_results function from the output_handler module
            save_results(job_data, file_format=output_config.get("file_format", "json"))
        elif not job_data:
            logging.info("No job data scraped, skipping save.") # Added clarification
        else:
             logging.info("File saving disabled in config.") # Added clarification


        # If execution reaches here without critical errors, mark as successful
        bot_success = True
        return True # Return True on successful completion of the try block

    except Exception as e:
        logging.critical(f"An unexpected error occurred in main flow: {e}", exc_info=True) # Log full traceback
        bot_success = False
        return False # Return False on major exception
    finally:
        # Ensure driver quits regardless of success/failure (original implicit behavior via main() ending)
        if driver:
            logging.info("Closing WebDriver.")
            driver.quit()
        logging.info("--- Bot Execution Finished ---") # Original log


# --- Execution Block (Copied from original) ---
if __name__ == "__main__":
    main() # Call the main function