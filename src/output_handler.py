# src/output_handler.py
import json
import logging
from datetime import datetime
import csv # Added for potential CSV output later

def save_results(job_data, file_format="json", filename_prefix="linkedin_jobs"):
    """Saves the scraped job data to a file."""
    if not job_data:
        logging.warning("No job data provided to save.")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_format = file_format.lower()
    filename = f"{filename_prefix}_{timestamp}.{file_format}"

    logging.info(f"Attempting to save {len(job_data)} jobs to {filename}...")

    try:
        if file_format == "json":
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, indent=2, ensure_ascii=False)
        elif file_format == "txt":
            with open(filename, 'w', encoding='utf-8') as f:
                for i, job in enumerate(job_data):
                    f.write(f"--- Job {i+1} ---\n")
                    f.write(f"Title: {job.get('title', 'N/A')}\n")
                    f.write(f"Company: {job.get('company', 'N/A')}\n")
                    f.write(f"Location: {job.get('location', 'N/A')}\n")
                    f.write(f"Posted: {job.get('date_posted', 'N/A')}\n")
                    f.write(f"URL: {job.get('url', 'N/A')}\n")
                    f.write(f"Easy Apply: {job.get('easy_apply', 'Unknown')}\n")
                    desc = job.get('description', 'N/A')
                    f.write(f"Description: {desc[:300]}...\n" if len(desc) > 300 else f"Description: {desc}\n")
                    f.write(f"Scraped At: {job.get('scraped_at', 'N/A')}\n")
                    f.write("-" * 20 + "\n\n")
        # Example for CSV (can be added as an option)
        # elif file_format == "csv":
        #     if not job_data: return False
        #     fieldnames = job_data[0].keys() # Assumes all dicts have same keys
        #     with open(filename, 'w', newline='', encoding='utf-8') as f:
        #         writer = csv.DictWriter(f, fieldnames=fieldnames)
        #         writer.writeheader()
        #         writer.writerows(job_data)
        else:
            logging.error(f"Unsupported file format specified: {file_format}. Supported formats: json, txt.")
            return False

        logging.info(f"Successfully saved job data to {filename}")
        return True

    except IOError as e:
         logging.error(f"File I/O error saving results to {filename}: {e}")
         return False
    except Exception as e:
        logging.error(f"An unexpected error occurred while saving results to {filename}: {e}")
        return False