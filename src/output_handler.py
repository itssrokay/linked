# src/output_handler.py
import json
import logging
from datetime import datetime
# No CSV import needed as it wasn't in the original save_results

# Directly copied from the provided code
def save_results(job_data, file_format="json"):
    """Saves the scraped job data to a file."""
    if not job_data:
        logging.warning("No job data to save.") # Original log
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # Original format

    if file_format.lower() == "json":
        filename = f"linkedin_jobs_{timestamp}.json" # Original filename format
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, indent=2, ensure_ascii=False) # Original dump settings
            logging.info(f"Job data saved to {filename}") # Original log
            return True
        except Exception as e:
            logging.error(f"Error saving job data to JSON: {e}") # Original log
            return False
    elif file_format.lower() == "txt":
        filename = f"linkedin_jobs_{timestamp}.txt" # Original filename format
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for job in job_data: # Original iteration and writing logic
                    f.write(f"Title: {job.get('title', 'Unknown')}\n")
                    f.write(f"Company: {job.get('company', 'Unknown')}\n")
                    f.write(f"Location: {job.get('location', 'Unknown')}\n")
                    f.write(f"Posted: {job.get('date_posted', 'Unknown')}\n")
                    f.write(f"URL: {job.get('url', '')}\n")
                    # Original description slicing and formatting
                    f.write(f"Description: {job.get('description', 'No description available')[:500]}...\n")
                    f.write("\n" + "-" * 80 + "\n\n")
            logging.info(f"Job data saved to {filename}") # Original log
            return True
        except Exception as e:
            logging.error(f"Error saving job data to TXT: {e}") # Original log
            return False
    else:
        logging.error(f"Unsupported file format: {file_format}") # Original log
        return False