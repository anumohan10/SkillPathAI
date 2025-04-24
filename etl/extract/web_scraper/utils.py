import time
import random
import os
import json
import logging
from filelock import FileLock
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..","..")))
from backend.database import get_snowflake_connection

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


# Configure logging with detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_headless_driver():
    """
    Create and return a Selenium WebDriver instance with headless Chrome.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    )
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info("ChromeDriver successfully initialized.")
    except Exception as e:
        logging.error("Error initializing ChromeDriver: %s", e)
        raise
    return driver

def save_json(data, output_file):
    """
    Append new course data to a JSON file.
    
    Args:
        data (dict): The course metadata to append (e.g., {"URL": "...", "course_language": "..."})
        output_file (str): Path to the JSON output file
    """
    # Initialize an empty list to hold all course data
    all_courses = []
    
    # Check if the file exists and load existing data
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                all_courses = json.load(f)
                # Ensure all_courses is a list (in case the file was malformed)
                if not isinstance(all_courses, list):
                    all_courses = []
        except (json.JSONDecodeError, IOError) as e:
            logging.error("Error reading JSON file %s: %s. Starting with an empty list.", output_file, e)
            all_courses = []
    
    # Handle both single dict and list of dicts
    if isinstance(data, dict):
        all_courses.append(data)
    elif isinstance(data, list):
        all_courses.extend(data)  # Extend with the list to keep it flat
    
    # Write the updated list back to the file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_courses, f, indent=2)
    
    logging.info("Appended data to %s. Total courses: %d", output_file, len(all_courses))
    # """
    # Write the data to a JSON file.
    # """
    # try:
    #     with open(output_file, 'w', encoding='utf-8') as f:
    #         json.dump(data, f, indent=2)

    #     logging.info("Data successfully written to %s", output_file)
    # except Exception as e:
    #     logging.error("Error writing JSON file (%s): %s", output_file, e)

def load_processed_links(cache_file):
    """
    Load and return a set of processed links from the cache file.
    """
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                processed = set(json.load(f))
            logging.info("Loaded %d processed links from %s", len(processed), cache_file)
            return processed
        except Exception as e:
            logging.error("Error reading cache file (%s): %s", cache_file, e)
            return set()
    else:
        logging.info("No cache file found. Starting with an empty cache.")
        return set()

def update_processed_links(cache_file, processed_links):
    """Update processed links JSON file with file locking."""
    lock = FileLock(f"{cache_file}.lock")
    with lock:
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(list(processed_links), f)
            logging.info("Cache updated with %d processed links to %s", len(processed_links), cache_file)
        except Exception as e:
            logging.error("Error updating cache file %s: %s", cache_file, e)

def retrieve_links(limit=100):
    """Fetch URLs from Snowflake."""
    conn = get_snowflake_connection()
    cur = conn.cursor()
    select_query = f"SELECT URL FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES LIMIT {limit};"
    cur.execute(select_query)
    df = cur.fetch_pandas_all()
    conn.close()
    return df

