from bs4 import BeautifulSoup
import json

# Step 1: Read the HTML file
try:
    with open("./tmp/computer-vision-nanodegree--nd891", "r", encoding="utf-8") as file:
        html_content = file.read()
    print("File read successfully. Length of HTML content:", len(html_content))
except FileNotFoundError:
    print("Error: File 'tmp/data-analyst-nanodegree--nd002' not found.")
    exit(1)
except Exception as e:
    print(f"Error reading file: {e}")
    exit(1)

# Step 2: Parse the HTML content with BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Diagnostic: Check if soup is valid and has content
print("Soup object created. Title tag:", soup.title)
if not soup.title:
    print("Warning: No <title> tag found in the HTML!")

# Step 3: Extract metadata with error handling
metadata = {}

# From <title>
# try:
#     metadata['Course Name'] = soup.title.string.split('|')[0].strip() if soup.title and soup.title.string else "N/A"
# except AttributeError:
#     metadata['Course Name'] = "N/A"
#     print("Error: Could not extract Course Name from <title>.")

# From <meta> tags
# meta_desc = soup.find('meta', {'name': 'description'})
# metadata['Description'] = meta_desc['content'] if meta_desc else "N/A"

meta_url = soup.find('meta', {'property': 'og:url'})
metadata['URL'] = meta_url['content'] if meta_url else "N/A"

# From JSON-LD structured data
script = soup.find('script', type='application/ld+json')
if script and script.string:
    try:
        json_data = json.loads(script.string)
        course = json_data['@graph'][1]  # Assuming the course is the second item in @graph
        metadata['Course Name'] = course.get('name', 'N/A')
        metadata['Description'] = course.get('description', 'N/A')
        metadata['Level'] = course.get('educationalLevel', 'N/A')
        metadata['Prerequisites'] = ', '.join(course.get('coursePrerequisites', []))
        metadata['Duration'] = course.get('hasCourseInstance', [{}])[0].get('courseWorkload', 'N/A')
        metadata['Language'] = course.get('inLanguage', 'N/A')
        metadata['Skills'] = ', '.join(course.get('about', []))
        metadata['Rating'] = course.get('aggregateRating', {}).get('ratingValue', 'N/A')
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error parsing JSON-LD: {e}")
        metadata.update({
            'Course Name': 'N/A',
            'Description': 'N/A',
            'Level': 'N/A',
            'Prerequisites': 'N/A',
            'Duration': 'N/A',
            'Language': 'N/A',
            'Skills': 'N/A',
            'Rating': 'N/A'
        })
else:
    print("Warning: No JSON-LD script found or it’s empty.")
    metadata.update({
        'Level': 'N/A',
        'Prerequisites': 'N/A',
        'Duration': 'N/A',
        'Language': 'N/A',
        'Skills': 'N/A'
    })

# Step 4: Print the extracted metadata
print(json.dumps(metadata, indent=2))
# ------------------------------------------------------------------------------------------
import time
import random
import os
import json
import logging

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
    except Exception as e:
        logging.error("Error initializing ChromeDriver: %s", e)
        raise
    return driver


def get_course_links(driver, catalog_url):
    """
    Retrieve and return a list of unique course link URLs from the catalog page.
    """
    try:
        driver.get(catalog_url)
        time.sleep(2)  # Allow page to load
        soup = BeautifulSoup(driver.page_source, "html.parser")
    except Exception as e:
        logging.error("Error loading catalog page: %s", e)
        return []

    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if "course/" in href:
            if not href.startswith("http"):
                href = "https://www.udacity.com" + href
            links.add(href)
    return list(links)


def parse_course_page(driver, course_url):
    """
    Fetch and return the HTML source of a course page.
    """
    try:
        driver.get(course_url)
        logging.info(f"Retrieved HTML page for {course_url}")
        time.sleep(random.uniform(2, 4))  # Mimic human browsing delay
        return driver.page_source
    except Exception as e:
        logging.error("Error fetching course page (%s): %s", course_url, e)
        return None


def extract_data(html_source):
    """
    Extract course metadata from HTML source and return it as a dictionary.
    """
    soup = BeautifulSoup(html_source, 'html.parser')
    metadata = {}

    meta_url = soup.find('meta', {'property': 'og:url'})
    metadata['URL'] = meta_url.get('content') if meta_url and meta_url.get('content') else "N/A"

    script = soup.find('script', type='application/ld+json')
    if script and script.string:
        try:
            json_data = json.loads(script.string)
            course = None
            # Handle JSON-LD structure variations
            if isinstance(json_data, dict) and '@graph' in json_data and isinstance(json_data['@graph'], list) and len(json_data['@graph']) > 1:
                course = json_data['@graph'][1]
            elif isinstance(json_data, dict):
                course = json_data

            if course:
                metadata['Course Name'] = course.get('name', 'N/A')
                metadata['Description'] = course.get('description', 'N/A')
                metadata['Level'] = course.get('educationalLevel', 'N/A')
                
                # Handle prerequisites which can be a list or a string
                prerequisites = course.get('coursePrerequisites', [])
                if isinstance(prerequisites, list):
                    metadata['Prerequisites'] = ', '.join(prerequisites)
                else:
                    metadata['Prerequisites'] = prerequisites if prerequisites else 'N/A'

                # Duration may be nested under a course instance list
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
            else:
                logging.warning("Course data not found in JSON-LD.")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logging.error("Error parsing JSON-LD: %s", e)
    else:
        logging.warning("No JSON-LD script found or it is empty.")
    
    return metadata


def save_json(data, output_file):
    """
    Write the data to a JSON file.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
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


def main():
    catalog_url = "https://www.udacity.com/catalog"
    output_json_file = "course_metadata.json"
    cache_file = "processed_links_cache.json"
    
    driver = create_headless_driver()
    all_metadata = []

    # Retrieve course links
    course_links = get_course_links(driver, catalog_url)
    logging.info("Found %d course links.", len(course_links))

    processed_links = load_processed_links(cache_file)

    for link in course_links:
        if link in processed_links:
            logging.info("Skipping already processed link: %s", link)
            continue

        html_source = parse_course_page(driver, link)
        if not html_source:
            continue

        course_metadata = extract_data(html_source)
        if course_metadata:
            all_metadata.append(course_metadata)
            # Use the URL from the metadata if available; fallback to the link itself
            processed_links.add(course_metadata.get('URL', link))

    # Save processed links and collected metadata
    update_processed_links(cache_file, processed_links)
    save_json(all_metadata, output_json_file)
    driver.quit()


if __name__ == "__main__":
    main()

# -------------------------------------------------------------------------------------------------------

import time
import random
import os
import json
import logging

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
    except Exception as e:
        logging.error("Error initializing ChromeDriver: %s", e)
        raise
    return driver


def get_course_links(driver, catalog_url):
    """
    Retrieve and return a list of unique course link URLs from the catalog page.
    """
    try:
        driver.get(catalog_url)
        time.sleep(2)  # Allow page to load
        soup = BeautifulSoup(driver.page_source, "html.parser")
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
    return list(links)


def parse_course_page(driver, course_url):
    """
    Fetch and return the HTML source of a course page.
    """
    try:
        driver.get(course_url)
        time.sleep(random.uniform(2, 4))  # Mimic human browsing delay
        return driver.page_source
    except Exception as e:
        logging.error("Error fetching course page (%s): %s", course_url, e)
        return None


def extract_data(html_source):
    """
    Extract course metadata from HTML source and return it as a dictionary.
    """
    soup = BeautifulSoup(html_source, 'html.parser')
    metadata = {}

    meta_url = soup.find('meta', {'property': 'og:url'})
    metadata['URL'] = meta_url.get('content') if meta_url and meta_url.get('content') else "N/A"

    script = soup.find('script', type='application/ld+json')
    if script and script.string:
        try:
            json_data = json.loads(script.string)
            course = None
            # Handle JSON-LD structure variations
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
            else:
                logging.warning("Course data not found in JSON-LD.")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logging.error("Error parsing JSON-LD: %s", e)
    else:
        logging.warning("No JSON-LD script found or it is empty.")
    
    return metadata


def save_json(data, output_file):
    """
    Write the data to a JSON file.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
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


def main():
    base_catalog_url = "https://www.udacity.com/catalog"
    output_json_file = "course_metadata.json"
    cache_file = "processed_links_cache.json"
    
    driver = create_headless_driver()
    all_metadata = []
    processed_links = load_processed_links(cache_file)

    # Loop through all 26 pages of the cataloghttps://www.udacity.com/catalog?page=page-2
    for page in range(1, 27):
        # Use query parameter for pages greater than 1; adjust as needed if the URL pattern differs
        catalog_url = f"{base_catalog_url}?page=page-{page}" if page > 1 else base_catalog_url
        logging.info("Processing catalog page: %s", catalog_url)
        
        course_links = get_course_links(driver, catalog_url)
        logging.info("Found %d course links on page %d.", len(course_links), page)

        for link in course_links:
            if link in processed_links:
                logging.info("Skipping already processed link: %s", link)
                continue

            html_source = parse_course_page(driver, link)
            if not html_source:
                continue

            course_metadata = extract_data(html_source)
            if course_metadata:
                all_metadata.append(course_metadata)
                processed_links.add(course_metadata.get('URL', link))

    update_processed_links(cache_file, processed_links)
    save_json(all_metadata, output_json_file)
    driver.quit()


if __name__ == "__main__":
    main()

#-------------------------------------------------------------------------------------------------------

# import time
# import random
# import os
# import json
# import logging

# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager

# # Configure logging with more detailed output
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )


# def create_headless_driver():
#     """
#     Create and return a Selenium WebDriver instance with headless Chrome.
#     """
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument(
#         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
#     )
#     try:
#         service = Service(ChromeDriverManager().install())
#         driver = webdriver.Chrome(service=service, options=chrome_options)
#         logging.info("ChromeDriver successfully initialized.")
#     except Exception as e:
#         logging.error("Error initializing ChromeDriver: %s", e)
#         raise
#     return driver


# def get_course_links(driver, catalog_url):
#     # """
#     # Retrieve and return a list of unique course link URLs from the catalog page.
#     # """
#     # try:
#     #     logging.info("Loading catalog URL: %s", catalog_url)
#     #     driver.get(catalog_url)
#     #     time.sleep(2)  # Allow page to load
#     #     soup = BeautifulSoup(driver.page_source, "html.parser")
#     # except Exception as e:
#     #     logging.error("Error loading catalog page (%s): %s", catalog_url, e)
#     #     return []

#     # links = set()
#     # for a_tag in soup.find_all("a", href=True):
#     #     href = a_tag["href"]
#     #     if "course/" in href:
#     #         if not href.startswith("http"):
#     #             href = "https://www.udacity.com" + href
#     #         links.add(href)
#     # logging.info("Found %d course links on page.", len(links))
#     # return list(links)
#     """
#     Fetch subcategory links and then course links from a Udemy catalog page.
#     """
#     try:
#         logging.info("Loading catalog URL: %s", catalog_url)
#         driver.get(catalog_url)
#         time.sleep(2)
#         soup = BeautifulSoup(driver.page_source, "html.parser")
#     except Exception as e:
#         logging.error("Error loading catalog page (%s): %s", catalog_url, e)
#         return []

#     # Step 1: Get subcategory links
#     category_links = set()
#     subcategory_nav = soup.find('nav', {'aria-label': 'Explore'})
#     if subcategory_nav:
#         for a_tag in subcategory_nav.find_all("a", href=True):
#             href = a_tag["href"]
#             if "/courses/development/" in href:
#                 if not href.startswith("http"):
#                     href = "https://www.udemy.com" + href
#                 subcategory_links.add(href)

#     logging.info("Found %d subcategory links on page.", len(subcategory_links))

#     # Step 2: Fetch course links from each subcategory (optional)
#     course_links = set()
#     for subcat_url in subcategory_links:
#         try:
#             html_source = parse_course_page(subcat_url)
#             if html_source:
#                 subcat_soup = BeautifulSoup(html_source, "html.parser")
#                 for a_tag in subcat_soup.find_all("a", href=True):
#                     href = a_tag["href"]
#                     if "/course/" in href and "draft" not in href:
#                         if not href.startswith("http"):
#                             href = "https://www.udemy.com" + href
#                         course_links.add(href)
#         except Exception as e:
#             logging.error("Error processing subcategory (%s): %s", subcat_url, e)

#     logging.info("Found %d course links across subcategories.", len(course_links))
#     return list(course_links)


# def parse_course_page(driver, course_url):
#     """
#     Fetch and return the HTML source of a course page.
#     """
#     try:
#         logging.info("Processing course URL: %s", course_url)
#         driver.get(course_url)
#         delay = random.uniform(2, 4)
#         logging.debug("Sleeping for %.2f seconds to mimic human browsing.", delay)
#         time.sleep(delay)
#         return driver.page_source
#     except Exception as e:
#         logging.error("Error fetching course page (%s): %s", course_url, e)
#         return None


# def extract_data(html_source):
#     """
#     Extract course metadata from HTML source and return it as a dictionary.
#     """
#     soup = BeautifulSoup(html_source, 'html.parser')
#     metadata = {}

#     meta_url = soup.find('meta', {'property': 'og:url'})
#     metadata['URL'] = meta_url.get('content') if meta_url and meta_url.get('content') else "N/A"

#     script = soup.find('script', type='application/ld+json')
#     if script and script.string:
#         try:
#             json_data = json.loads(script.string)
#             course = None
#             # Handle JSON-LD structure variations
#             if isinstance(json_data, dict) and '@graph' in json_data and isinstance(json_data['@graph'], list) and len(json_data['@graph']) > 1:
#                 course = json_data['@graph'][1]
#             elif isinstance(json_data, dict):
#                 course = json_data

#             if course:
#                 metadata['Course Name'] = course.get('name', 'N/A')
#                 metadata['Description'] = course.get('description', 'N/A')
#                 metadata['Level'] = course.get('educationalLevel', 'N/A')
                
#                 prerequisites = course.get('coursePrerequisites', [])
#                 if isinstance(prerequisites, list):
#                     metadata['Prerequisites'] = ', '.join(prerequisites)
#                 else:
#                     metadata['Prerequisites'] = prerequisites if prerequisites else 'N/A'

#                 course_instances = course.get('hasCourseInstance', [])
#                 if isinstance(course_instances, list) and course_instances:
#                     metadata['Duration'] = course_instances[0].get('courseWorkload', 'N/A')
#                 else:
#                     metadata['Duration'] = 'N/A'
                
#                 metadata['Language'] = course.get('inLanguage', 'N/A')
#                 about = course.get('about', [])
#                 if isinstance(about, list):
#                     metadata['Skills'] = ', '.join(about)
#                 else:
#                     metadata['Skills'] = about if about else 'N/A'
#                 aggregate_rating = course.get('aggregateRating', {})
#                 metadata['Rating'] = aggregate_rating.get('ratingValue', 'N/A')

#                 logging.info("Extracted course: %s", metadata.get('Course Name', 'N/A'))
#             else:
#                 logging.warning("Course data not found in JSON-LD.")
#         except (json.JSONDecodeError, KeyError, IndexError) as e:
#             logging.error("Error parsing JSON-LD: %s", e)
#     else:
#         logging.warning("No JSON-LD script found or it is empty.")
    
#     return metadata


# def save_json(data, output_file):
#     """
#     Write the data to a JSON file.
#     """
#     try:
#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(data, f, indent=2)
#         logging.info("Data successfully written to %s", output_file)
#     except Exception as e:
#         logging.error("Error writing JSON file (%s): %s", output_file, e)


# def load_processed_links(cache_file):
#     """
#     Load and return a set of processed links from the cache file.
#     """
#     if os.path.exists(cache_file):
#         try:
#             with open(cache_file, 'r', encoding='utf-8') as f:
#                 processed = set(json.load(f))
#             logging.info("Loaded %d processed links from %s", len(processed), cache_file)
#             return processed
#         except Exception as e:
#             logging.error("Error reading cache file (%s): %s", cache_file, e)
#             return set()
#     else:
#         logging.info("No cache file found. Starting with an empty cache.")
#         return set()


# def update_processed_links(cache_file, processed_links):
#     """
#     Update the cache file with the set of processed links.
#     """
#     try:
#         with open(cache_file, 'w', encoding='utf-8') as f:
#             json.dump(list(processed_links), f)
#         logging.info("Cache updated with %d processed links.", len(processed_links))
#     except Exception as e:
#         logging.error("Error updating cache file (%s): %s", cache_file, e)


# def main():
#     base_catalog_url = "https://www.udemy.com/courses/development/"
#     output_json_file = "udemy_course_metadata.json"
#     cache_file = "udemy_processed_links_cache.json"
    
    
#     cur = conn.cursor()

#     retrieve_url = "SELECT URL FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES ORDER BY COURSE_ID"
#     cur.execute(retrieve_url)
#     df = cur.fetch_pandas_all()

    

#     driver = create_headless_driver()
#     all_metadata = []
#     processed_links_cache = load_processed_links(cache_file)

#     # Loop through all 26 pages of the catalog
#     for page in range(1, 5):
#         if page == 1:
#             catalog_url = base_catalog_url
#         else:
#             catalog_url = f"{base_catalog_url}?page=page-{page}"
#         logging.info("Processing catalog page %d: %s", page, catalog_url)
        
#         course_links = get_course_links(driver, catalog_url)
#         logging.info("Found %d course links on catalog page %d.", len(course_links), page)

#         for link in course_links:
#             if link in processed_links_cache:
#                 logging.info("Skipping already processed link: %s", link)
#                 continue

#             html_source = parse_course_page(driver, link)
#             if not html_source:
#                 logging.warning("Skipping link due to empty HTML source: %s", link)
#                 continue

#             course_metadata = extract_data(html_source)
#             if course_metadata:
#                 all_metadata.append(course_metadata)
#                 processed_links_cache.add(course_metadata.get('URL', link))
#             else:
#                 logging.warning("No metadata extracted for link: %s", link)

#     update_processed_links(cache_file, processed_links_cache)
#     save_json(all_metadata, output_json_file)
#     driver.quit()
#     logging.info("Scraping completed. Total courses processed: %d", len(all_metadata))


# if __name__ == "__main__":
#     main()
