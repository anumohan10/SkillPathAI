# scrapers/edx.py
import time
import random
import json
import logging
from bs4 import BeautifulSoup
from .base import CourseScraper

class EdxScraper(CourseScraper):
    def get_catalog_url(self, page_number):
        """
        Build the edX catalog URL.
        Example: "https://www.edx.org/search?tab=course&page=2"
        """
        return f"{self.base_catalog_url}?tab=course&page={page_number}"

    def get_course_links(self, catalog_url):
        try:
            logging.info("Loading catalog URL: %s", catalog_url)
            self.driver.get(catalog_url)
            time.sleep(2)  # Allow page to load
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
        except Exception as e:
            logging.error("Error loading catalog page (%s): %s", catalog_url, e)
            return []

        links = set()
        # Update logic as per edX page structure; here we assume course URLs contain "/course/"
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if "/course/" in href:
                if not href.startswith("http"):
                    href = "https://www.edx.org" + href
                links.add(href)
        logging.info("Found %d course links on edX page.", len(links))
        return list(links)

    def parse_course_page(self, course_url):
        try:
            logging.info("Processing edX course URL: %s", course_url)
            self.driver.get(course_url)
            delay = random.uniform(2, 4)
            logging.debug("Sleeping for %.2f seconds.", delay)
            time.sleep(delay)
            return self.driver.page_source
        except Exception as e:
            logging.error("Error fetching course page (%s): %s", course_url, e)
            return None

    def extract_data(self, html_source):
        soup = BeautifulSoup(html_source, 'html.parser')
        metadata = {}

        meta_url = soup.find('meta', {'property': 'og:url'})
        metadata['URL'] = meta_url.get('content') if meta_url and meta_url.get('content') else "N/A"

        # For edX, adjust extraction as needed.
        script = soup.find('script', type='application/ld+json')
        if script and script.string:
            try:
                json_data = json.loads(script.string)
                metadata['Course Name'] = json_data.get('name', 'N/A')
                metadata['Description'] = json_data.get('description', 'N/A')
                metadata['Level'] = json_data.get('educationalLevel', 'N/A')
                metadata['Prerequisites'] = json_data.get('coursePrerequisites', 'N/A')
                metadata['Duration'] = json_data.get('timeRequired', 'N/A')
                metadata['Language'] = json_data.get('inLanguage', 'N/A')
                about = json_data.get('about', [])
                if isinstance(about, list):
                    metadata['Skills'] = ', '.join(about)
                else:
                    metadata['Skills'] = about if about else 'N/A'
                logging.info("Extracted edX course: %s", metadata.get('Course Name', 'N/A'))
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logging.error("Error parsing JSON-LD in edX course page: %s", e)
        else:
            logging.warning("No JSON-LD script found or it is empty in edX course page.")
        return metadata
