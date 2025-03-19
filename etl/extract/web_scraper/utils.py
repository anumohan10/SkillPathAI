import time
import random
import os
import json
import logging

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
    Write the data to a JSON file.
    """
    try:
        with open(output_file, 'a', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logging.info("Data successfully written to %s", output_file)
    except Exception as e:
        logging.error("Error writing JSON file (%s): %s", output_file, e)

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
    """
    Update the cache file with the set of processed links.
    """
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(list(processed_links), f)
        logging.info("Cache updated with %d processed links.", len(processed_links))
    except Exception as e:
        logging.error("Error updating cache file (%s): %s", cache_file, e)
