import time
import random
import json
import logging
from bs4 import BeautifulSoup
from .base import CourseScraper

class UdemyScraper(CourseScraper):
    def get_catalog_url(self, page_number):
        """
        Build the Udemy catalog URL with pagination.
        Example: "https://www.udemy.com/courses/?p=2"
        """
        return f"{self.base_catalog_url}?p={page_number}"

    def get_course_links(self, catalog_url):
        """
        Fetch course links from a Udemy catalog page.
        """
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
            if "/course/" in href and "draft" not in href:  # Exclude draft courses
                if not href.startswith("http"):
                    href = "https://www.udemy.com" + href
                links.add(href)
        logging.info("Found %d course links on page.", len(links))
        return list(links)

    def parse_course_page(self, course_url):
        """
        Fetch and return the HTML source of a Udemy course page.
        """
        try:
            logging.info("Processing Udemy course URL: %s", course_url)
            self.driver.get(course_url)
            delay = random.uniform(2, 4)
            logging.debug("Sleeping for %.2f seconds.", delay)
            time.sleep(delay)
            return self.driver.page_source
        except Exception as e:
            logging.error("Error fetching course page (%s): %s", course_url, e)
            return None

    def extract_data(self, html_source):
        """
        Extract course metadata from Udemy HTML source.
        """
        soup = BeautifulSoup(html_source, 'html.parser')
        metadata = {}

        # URL
        meta_url = soup.find('meta', {'property': 'og:url'})
        metadata['URL'] = meta_url.get('content') if meta_url and meta_url.get('content') else "N/A"

        # Extract from <head> meta tags
        metadata['Title'] = (
            soup.title.string.strip() if soup.title and soup.title.string
            else soup.find('meta', {'property': 'og:title'}).get('content', 'N/A')
        )
        metadata['Description'] = (
            soup.find('meta', {'name': 'description'}).get('content') or
            soup.find('meta', {'property': 'og:description'}).get('content', 'N/A')
        )

        # Extract from data-module-args in <body>
        body = soup.find('body')
        if body and body.get('data-module-args'):
            try:
                module_args = json.loads(body['data-module-args'])
                course_data = module_args.get('serverSideProps', {}).get('course', {})

                # Skills (from objectives)
                objectives = course_data.get('objectives', [])
                metadata['Skills'] = "\n".join(objectives) if objectives else "N/A"

                # Level
                metadata['Level'] = course_data.get('instructionalLevel', 'N/A')

                # Prerequisites
                prereqs = course_data.get('prerequisites', [])
                metadata['Prerequisites'] = "\n".join(prereqs) if prereqs else "N/A"

                # Duration (convert seconds to hours/minutes)
                content_length = course_data.get('contentLengthVideo', 0)
                if content_length:
                    hours = content_length // 3600
                    minutes = (content_length % 3600) // 60
                    metadata['Duration'] = f"{hours}h {minutes}m" if hours else f"{minutes}m"
                else:
                    metadata['Duration'] = "N/A"

                # Language
                languages = course_data.get('captionedLanguages', ['N/A'])
                metadata['Language'] = ", ".join(languages) if languages else course_data.get('localeSimpleEnglishTitle', 'N/A')

                # Average Rating
                metadata['Average Rating'] = course_data.get('rating', 'N/A')

                logging.info("Extracted Udemy course: %s", metadata.get('Title', 'N/A'))
            except json.JSONDecodeError as e:
                logging.error("Error parsing data-module-args JSON: %s", e)
                metadata.update({
                    'Skills': 'N/A',
                    'Level': 'N/A',
                    'Prerequisites': 'N/A',
                    'Duration': 'N/A',
                    'Language': 'N/A',
                    'Average Rating': 'N/A'
                })
        else:
            logging.warning("No data-module-args found in Udemy course page.")
            metadata.update({
                'Skills': 'N/A',
                'Level': 'N/A',
                'Prerequisites': 'N/A',
                'Duration': 'N/A',
                'Language': 'N/A',
                'Average Rating': 'N/A'
            })

        return metadata