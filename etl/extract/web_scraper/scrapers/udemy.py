# scrapers/udemy.py
import time
import random
import json
import logging
from utils import create_headless_driver, save_json, update_processed_links
from concurrent.futures import ProcessPoolExecutor, as_completed
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from .base import CourseScraper

class UdemyScraper(CourseScraper):
    def __init__(self, driver, base_catalog_url):
        super().__init__(driver, base_catalog_url)
        self.max_retries = 3
        self.batch_size = 1000  # Process 1K URLs per batch
        self.max_workers = 6    # Adjust based on system capacity

    def get_catalog_url(self):
        """
        Build the Udemy catalog URL with pagination.
        Example: "https://www.udemy.com/courses/?p=2"
        """
        pass

    def get_course_links(self, course_urls):
        """
        Fetch course links from a Udemy catalog page.
        """
        course_urls["URL"] = "https://www.udemy.com" + course_urls['URL']
        return course_urls["URL"].tolist()

    def parse_course_page(self, driver, course_url, retries=0):
        """
        Fetch and return the HTML source of a Udemy course page.
        """
        try:
            logging.info("Processing Udemy course URL: %s (Attempt %d/%d)", course_url, retries + 1, self.max_retries)
            flag = True
            while flag:
                driver.get(course_url)
                logging.info("Current URL:\n"+driver.current_url)
                if (driver.current_url == course_url):
                    flag = False
                    delay = random.uniform(1, 3)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//meta[@property="og:url"]'))
            )
            delay = random.uniform(2, 5)
            logging.debug("Sleeping for %.2f seconds.", delay)
            time.sleep(delay)
            try:
                meta_tag = driver.find_element(By.CSS_SELECTOR, f"meta[property='og:url']")
                logging.info("Retrieved URL:\n"+meta_tag.get_attribute("content"))
            except Exception as e:
                logging.error(f"Error extracting URL: {e}")
            try:
                # Locate the element using its data-purpose attribute
                locale_element = driver.find_element(By.CSS_SELECTOR, "div[data-purpose='lead-course-locale']")
                # Retrieve the visible text and strip any extra whitespace
                course_language = locale_element.text.strip()
                logging.info(f"Course Language: {course_language}")
            except Exception as e:
                logging.error(f"Error extracting course language: {e}")
            return driver.page_source
        except Exception as e:
            logging.error("Error fetching course page (%s): %s", course_url, e)
            return None

    def extract_data(self, html_source):
        """
        Extract course metadata from Udemy HTML source.
        """
        soup = BeautifulSoup(html_source, 'html.parser')
        metadata = {}
        meta_url = soup.find('meta', {'property': 'og:url'})
        metadata['URL'] = meta_url.get('content') if meta_url and meta_url.get('content') else "N/A"

       # Find the div with class "clp-lead__locale"
        locale_div = soup.find('div', class_='clp-lead__locale')

        # Extract the text content, stripping the SVG element
        if locale_div:
            # Get the text after removing the SVG (first child)
            metadata["course_language"] = locale_div.text.strip()
            logging.info(f"Course Language: {metadata["course_language"]}")
        else:
            logging.info("Could not find the course language element.")
            metadata["course_language"] = "N/A"

        return metadata
    
    def scrape_single_url(self, url):
        driver = create_headless_driver()
        try:
            html_source = self.parse_course_page(driver, url)
            if not html_source:
                logging.warning("Skipping %s due to empty HTML source", url)
                return None
            metadata = self.extract_data(html_source)
            return metadata
        finally:
            driver.quit()

    def process_catalog_pages(self, processed_links_cache, course_links, output_json_file):
        """
        Process a catalog page and return a list of course metadata dictionaries.
        """

        course_links = self.get_course_links(course_links)
        logging.info("Total course links found: %d", len(course_links))

        urls_to_process = [url for url in course_links if url not in processed_links_cache]
        logging.info("URLs to process after filtering: %d", len(urls_to_process))

        if not urls_to_process:
            logging.info("No new URLs to process.")
            return []

        all_results = []
        for i in range(0, len(urls_to_process), self.batch_size):
            batch = urls_to_process[i:i + self.batch_size]
            logging.info("Processing batch %d-%d of %d URLs", i, i + len(batch), len(urls_to_process))

            results = []
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_url = {executor.submit(self.scrape_single_url, url): url for url in batch}
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        metadata = future.result()
                        if metadata:
                            results.append(metadata)
                            processed_links_cache.add(url)
                            logging.info("Processed and cached: %s", url)
                    except Exception as e:
                        logging.error("Exception for %s: %s", url, e)

            if results:
                save_json(results, output_json_file)
                all_results.extend(results)
            update_processed_links(output_json_file.replace("_course_metadata.json", "_processed_links_cache.json"), 
                                 processed_links_cache)
            logging.info("Checkpoint: Processed %d URLs total", len(processed_links_cache))
            return len(all_results)


        
