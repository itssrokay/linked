# main.py
import os
import logging
from dotenv import load_dotenv

# Setup logging first
from src.utils.logger_setup import setup_logging
setup_logging()

# Import necessary functions from modules
from src.config_loader import load_config, DEFAULT_CONFIG
from src.driver_setup import setup_driver
from src.linkedin_actions.login import login_with_retry
from src.linkedin_actions.navigation import navigate_to_jobs_page
from src.linkedin_actions.search_filter import perform_job_search, apply_filters
from src.linkedin_actions.scrape import scrape_jobs_on_page
from src.output_handler import save_results
from src.utils.helpers import human_delay

# --- Constants ---
CONFIG_FILE_PATH = "config/config.json"
ENV_FILE_PATH = "config/.env"


def main_bot_flow():
    """Main execution function for the LinkedIn Bot."""
    logging.info("--- LinkedIn Bot Initializing ---")

    # Load environment variables (Credentials)
    # Load from the specific path inside the config folder
    dotenv_path = os.path.join(os.path.dirname(__file__), ENV_FILE_PATH)
    if os.path.exists(dotenv_path):
         load_dotenv(dotenv_path=dotenv_path)
         logging.info(f"Loaded environment variables from: {dotenv_path}")
    else:
         logging.warning(f"Environment file not found at: {dotenv_path}. Attempting to load from default location.")
         load_dotenv() # Try loading from CWD or standard locations

    LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
    LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        logging.critical("CRITICAL: LinkedIn credentials (LINKEDIN_EMAIL, LINKEDIN_PASSWORD) not found in environment variables.")
        logging.critical(f"Ensure they are set in '{ENV_FILE_PATH}' or your system environment.")
        return False

    # Load configuration (Search criteria, filters, etc.)
    config = load_config(CONFIG_FILE_PATH)

    # Setup WebDriver
    driver = setup_driver()
    if not driver:
        logging.critical("Failed to initialize WebDriver. Bot cannot continue.")
        return False

    all_scraped_jobs = []
    success = False
    try:
        # 1. Login to LinkedIn
        if not login_with_retry(driver, LINKEDIN_EMAIL, LINKEDIN_PASSWORD):
            logging.critical("Login failed after multiple attempts. Exiting.")
            return False # Stop execution if login fails

        # 2. Navigate to Jobs page
        if not navigate_to_jobs_page(driver):
            logging.error("Failed to navigate to the Jobs page. Exiting.")
            return False

        # Wait for page elements (e.g., search boxes) to be ready
        human_delay(2.0, 4.0)

        # 3. Perform Job Search
        search_criteria = config.get("search_criteria", DEFAULT_CONFIG["search_criteria"])
        keywords = search_criteria.get("keywords", DEFAULT_CONFIG["search_criteria"]["keywords"])
        location = search_criteria.get("location", DEFAULT_CONFIG["search_criteria"]["location"])

        if not perform_job_search(driver, keywords, location):
            logging.error("Failed to perform the initial job search. Exiting.")
            return False

        # 4. Apply Filters
        filters = config.get("filters", DEFAULT_CONFIG["filters"])
        apply_filters(driver,
                      date_posted=filters.get("date_posted"),
                      experience_levels=filters.get("experience_level"))

        # 5. Scrape Job Listings (Potentially multiple pages later)
        # For now, just scraping the first page as per the provided scrape function logic
        scraping_config = config.get("scraping", DEFAULT_CONFIG["scraping"])
        # TODO: Implement pagination logic if max_pages > 1
        logging.info("Starting scraping process...")
        page_jobs = scrape_jobs_on_page(driver, easy_apply_only=scraping_config.get("easy_apply_only", True))
        all_scraped_jobs.extend(page_jobs)

        logging.info(f"Total jobs scraped: {len(all_scraped_jobs)}")

        # 6. Save Results
        output_config = config.get("output", DEFAULT_CONFIG["output"])
        if output_config.get("save_to_file", True) and all_scraped_jobs:
            save_results(all_scraped_jobs,
                         file_format=output_config.get("file_format", "json"),
                         filename_prefix=f"linkedin_jobs_{keywords.replace(' ','_')[:15]}")
        elif not all_scraped_jobs:
             logging.info("No jobs were scraped, skipping file saving.")
        else:
             logging.info("File saving is disabled in the configuration.")

        success = True # Mark as successful if reached here without critical errors

    except Exception as e:
        logging.critical(f"An unhandled critical error occurred during the main bot flow: {e}", exc_info=True)
        try:
            # Attempt to save screenshot on critical failure
            driver.save_screenshot(f"critical_error_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
            logging.info("Saved screenshot due to critical error.")
        except:
            logging.error("Failed to save screenshot during critical error handling.")
        success = False # Explicitly mark as failed
    finally:
        # 7. Cleanup: Close the WebDriver
        if driver:
            logging.info("Closing WebDriver...")
            driver.quit()
            logging.info("WebDriver closed.")

    logging.info(f"--- LinkedIn Bot Execution Finished (Success: {success}) ---")
    return success


if __name__ == "__main__":
    main_bot_flow()