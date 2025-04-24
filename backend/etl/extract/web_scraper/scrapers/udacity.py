# scrapers/udacity.py
import time
import random
import json
import logging
from bs4 import BeautifulSoup
from .base import CourseScraper

class UdacityScraper(CourseScraper):
    def get_catalog_url(self, page_number):
        """
        Build the Udacity catalog URL.
        Example: "https://www.udacity.com/catalog?page=page-2"
        """
        return f"{self.base_catalog_url}?page=page-{page_number}"

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
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if "course/" in href:
                if not href.startswith("http"):
                    href = "https://www.udacity.com" + href
                links.add(href)
        logging.info("Found %d course links on page.", len(links))
        return list(links)

    def parse_course_page(self, course_url):
        try:
            logging.info("Processing Udacity course URL: %s", course_url)
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

        script = soup.find('script', type='application/ld+json')
        if script and script.string:
            try:
                json_data = json.loads(script.string)
                course = None
                if isinstance(json_data, dict) and '@graph' in json_data and isinstance(json_data['@graph'], list) and len(json_data['@graph']) > 1:
                    course = json_data['@graph'][1]
                elif isinstance(json_data, dict):
                    course = json_data

                if course:
                    metadata['Course Name'] = course.get('name', 'N/A')
                    metadata['Description'] = course.get('description', 'N/A')
                    metadata['Level'] = course.get('educationalLevel', 'N/A')
                    
                    prerequisites = course.get('coursePrerequisites', [])
                    if isinstance(prerequisites, list):
                        metadata['Prerequisites'] = ', '.join(prerequisites)
                    else:
                        metadata['Prerequisites'] = prerequisites if prerequisites else 'N/A'

                    course_instances = course.get('hasCourseInstance', [])
                    if isinstance(course_instances, list) and course_instances:
                        metadata['Duration'] = course_instances[0].get('courseWorkload', 'N/A')
                    else:
                        metadata['Duration'] = 'N/A'
                    
                    metadata['Language'] = course.get('inLanguage', 'N/A')
                    about = course.get('about', [])
                    if isinstance(about, list):
                        metadata['Skills'] = ', '.join(about)
                    else:
                        metadata['Skills'] = about if about else 'N/A'
                    aggregate_rating = course.get('aggregateRating', {})
                    metadata['Rating'] = aggregate_rating.get('ratingValue', 'N/A')

                    logging.info("Extracted Udacity course: %s", metadata.get('Course Name', 'N/A'))
                else:
                    logging.warning("Course data not found in JSON-LD for Udacity.")
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logging.error("Error parsing JSON-LD in Udacity course page: %s", e)
        else:
            logging.warning("No JSON-LD script found or it is empty in Udacity course page.")
        
        return metadata
