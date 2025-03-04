# scrapers/base.py
from abc import ABC, abstractmethod
import logging

class CourseScraper(ABC):
    """
    Abstract base class for course scrapers.
    """
    def __init__(self, driver, base_catalog_url):
        self.driver = driver
        self.base_catalog_url = base_catalog_url

    @abstractmethod
    def get_catalog_url(self, page_number):
        """
        Return the catalog URL for the given page number.
        """
        pass

    @abstractmethod
    def get_course_links(self, catalog_url):
        """
        Retrieve and return a list of course link URLs from the catalog page.
        """
        pass

    @abstractmethod
    def parse_course_page(self, course_url):
        """
        Fetch and return the HTML source of a course page.
        """
        pass

    @abstractmethod
    def extract_data(self, html_source):
        """
        Extract course metadata from HTML source and return it as a dictionary.
        """
        pass

    def process_catalog_page(self, page_number):
        """
        Process a catalog page and return a list of course metadata dictionaries.
        """
        catalog_url = self.get_catalog_url(page_number)
        logging.info("Processing catalog page %d: %s", page_number, catalog_url)

        course_links = self.get_course_links(catalog_url)
        logging.info("Found %d course links on catalog page %d.", len(course_links), page_number)

        page_metadata = []
        for link in course_links:
            logging.info("Processing course link: %s", link)
            html_source = self.parse_course_page(link)
            if not html_source:
                logging.warning("Skipping link due to empty HTML source: %s", link)
                continue
            course_metadata = self.extract_data(html_source)
            if course_metadata:
                page_metadata.append(course_metadata)
            else:
                logging.warning("No metadata extracted for link: %s", link)
        return page_metadata
