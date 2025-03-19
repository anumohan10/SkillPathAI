# # import asyncio

# # from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext


# # async def main() -> None:
# #     crawler = PlaywrightCrawler(
# #         max_requests_per_crawl=5,  # Limit the crawl to 5 requests at most.
# #         headless=False,  # Show the browser window.
# #         browser_type='firefox',  # Use the Firefox browser.
# #     )

# #     # Define the default request handler, which will be called for every request.
# #     @crawler.router.default_handler
# #     async def request_handler(context: PlaywrightCrawlingContext) -> None:
# #         context.log.info(f'Processing {context.request.url} ...')

# #         # Extract and enqueue all links found on the page.
# #         await context.enqueue_links()

# #         # Extract data from the page using Playwright API.
# #         data = {
# #             'url': context.request.url,
# #             'title': await context.page.title(),
# #             'content': (await context.page.content())[:100],
# #         }

# #         # Push the extracted data to the default dataset.
# #         await context.push_data(data)

# #     # Run the crawler with the initial list of URLs.
# #     await crawler.run(['https://www.udacity.com/catalog'])

# #     # Export the entire dataset to a JSON file.
# #     await crawler.export_data('results.json')

# #     # Or work with the data directly.
# #     data = await crawler.get_data()
# #     crawler.log.info(f'Extracted data: {data.items}')


# # if __name__ == '__main__':
# #     asyncio.run(main())

# import time
# import random
# import os

# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager

# import json


# def create_headless_driver():
#     """
#     Create and return a Selenium WebDriver instance with headless Chrome.
#     """
#     chrome_options = Options()
#     # Enable headless mode
#     chrome_options.add_argument("--headless")
#     # Some additional flags that may reduce detection
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     # Set a custom user-agent string to appear more like a real browser
#     chrome_options.add_argument(
#         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
#     )

#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=chrome_options)
#     return driver


# def get_course_links(driver, catalog_url):
#     """
#     Navigates to the catalog_url and returns a list of unique course link URLs.
#     """
#     # Go to the catalog page
#     driver.get(catalog_url)
#     time.sleep(2)  # Let the page load

#     # Parse the rendered HTML
#     soup = BeautifulSoup(driver.page_source, "html.parser")

#     # Example: This logic may differ depending on site structure
#     # For Udacity, "course-card" might be a class that encloses each course
#     links = []
#     for a_tag in soup.find_all("a", href=True):
#         href = a_tag["href"]
#         # Check for typical course patterns in URL
#         # Adjust the pattern ("course/") to fit the site structure
#         if "course/" in href:
#             # Ensure full URL
#             if href.startswith("http"):
#                 full_link = href
#             else:
#                 # If relative, combine with the base URL
#                 full_link = "https://www.udacity.com" + href
#             links.append(full_link)
            
#     return list(set(links))  # remove duplicates


# def parse_course_page(driver, course_url):
#     """
#     Navigates to a single course page using Selenium, then parses out
#     relevant information. Returns a dictionary of extracted data.
#     """

#     # Visit course page
#     driver.get(course_url)
#     time.sleep(random.uniform(2, 4))  # random delay to mimic human browsing

#     # Grab the HTML source
#     page_source = driver.page_source
#     # soup = BeautifulSoup(page_source, "html.parser")
    
#     # Extract course-related data
#     # NOTE: The actual HTML structure of the site can vary.
#     # Adjust the find/find_all logic according to the site’s structure.
    
    
#     # Example extraction heuristics:
#     # 1. Course Title
#     # title_elem = soup.find("h1")
#     # if title_elem:
#     #     data["title"] = title_elem.get_text(strip=True)
#     # else:
#     #     data["title"] = "N/A"

#     # # 2. Course Overview or Description
#     # desc_elem = soup.find("p")  # or a more specific container
#     # if desc_elem:
#     #     data["description"] = desc_elem.get_text(" ", strip=True)
#     # else:
#     #     data["description"] = "N/A"

#     # # 3. Additional fields: e.g., Skill tags, Duration, Level, Language, etc.
#     # # This will heavily depend on the site’s DOM structure.
#     # # Example placeholders:
#     # data["skills"] = []
#     # data["duration"] = "N/A"
#     # data["prerequisites"] = "N/A"
#     # data["level"] = "N/A"
#     # data["language"] = "N/A"

#     # You can add AI-based parsing if needed. For instance:
#     #
#     #   - Send the entire page_source or relevant chunks to an LLM API
#     #   - Or train a custom model to pick out these fields
#     #
#     # data.update(extract_fields_with_ai(page_source))

#     # return data
#     return page_source

# def extract_data(soup, all_metadata, processed_links_cache):
#     metadata = {}
#     meta_url = soup.find('meta', {'property': 'og:url'})
#     metadata['URL'] = meta_url['content'] if meta_url else "N/A"

#     # From JSON-LD structured data
#     script = soup.find('script', type='application/ld+json')
#     if script and script.string:
#         try:
#             json_data = json.loads(script.string)
#             course = json_data['@graph'][1]  # Assuming the course is the second item in @graph
#             metadata['Course Name'] = course.get('name', 'N/A')
#             metadata['Description'] = course.get('description', 'N/A')
#             metadata['Level'] = course.get('educationalLevel', 'N/A')
#             metadata['Prerequisites'] = ', '.join(course.get('coursePrerequisites', []))
#             metadata['Duration'] = course.get('hasCourseInstance', [{}])[0].get('courseWorkload', 'N/A')
#             metadata['Language'] = course.get('inLanguage', 'N/A')
#             metadata['Skills'] = ', '.join(course.get('about', []))
#             metadata['Rating'] = course.get('aggregateRating', {}).get('ratingValue', 'N/A')
#         except (json.JSONDecodeError, KeyError, IndexError) as e:
#             print(f"Error parsing JSON-LD: {e}")
#             metadata.update({
#                 'Course Name': 'N/A',
#                 'Description': 'N/A',
#                 'Level': 'N/A',
#                 'Prerequisites': 'N/A',
#                 'Duration': 'N/A',
#                 'Language': 'N/A',
#                 'Skills': 'N/A',
#                 'Rating': 'N/A'
#             })
#     else:
#         print("Warning: No JSON-LD script found or it’s empty.")
#         metadata.update({
#             'Level': 'N/A',
#             'Prerequisites': 'N/A',
#             'Duration': 'N/A',
#             'Language': 'N/A',
#             'Skills': 'N/A'
#         })

#     all_metadata.append(metadata)
#     processed_links_cache.add(metadata['URL'])
#     # Step 4: Print the extracted metadata
#     print(json.dumps(metadata, indent=2))

# def log_course_url(processed_links_cache):
#     cache_file = "processed_links_cache.json"
#     try:
#         with open(cache_file, 'w', encoding='utf-8') as f:
#             json.dump(list(processed_links_cache), f)
#         print(f"Updated cache saved to {cache_file}. Total processed files: {len(processed_links_cache)}")
#     except Exception as e:
#         print(f"Error saving cache file: {e}")
#         exit(1)

# def load_processed_links(cache_file):
#     if os.path.exists(cache_file):
#         with open(cache_file, 'r', encoding='utf-8') as f:
#             processed_links_cache = set(json.load(f))
#         print(f"Loaded cache from {cache_file}. Number of previously processed files: {len(processed_links_cache)}")
#     else:
#         processed_links_cache = set()
#         print(f"No cache file found. Starting with empty cache.")
#     return processed_links_cache

# def main():
#     catalog_url = "https://www.udacity.com/catalog"

#     # Create the headless browser driver
#     driver = create_headless_driver()
#     output_json_file = "course_metadata.json"
#     cache_file = "processed_links_cache.json"
#     all_metadata = []
#     try:
#         # 1. Retrieve all course links from the catalog page
#         course_links = get_course_links(driver, catalog_url)
#         print(f"Found {len(course_links)} course links.")

#         # 2. Visit each course link and scrape data
        
#         processed_links_cache = load_processed_links(cache_file)

#         for link in course_links:
#             try:
#                 if link in processed_links_cache:
#                     print(f"Skipping {link}: Already processed (found in cache).")
#                     continue
#                 course_data = parse_course_page(driver, link)
#                 soup = BeautifulSoup(course_data, 'html.parser')
#                 extract_data(soup, all_metadata, processed_links_cache)
#                 log_course_url(processed_links_cache)
#                 # file_name = link.rsplit('/', 1)[-1]
#                 # with open("tmp/"+file_name, "x", encoding="utf-8") as file:
#                 #     file.write(str(soup.prettify()))
#                 # print(f"Content scraped from {link} ")

#                 # print(f"Scraped: {course_data['title']} from {link}")
#             except Exception as e:
#                 print(f"Error scraping {link}: {e}")
#         try:
#             with open(output_json_file, 'w', encoding='utf-8') as json_file:
#                 json.dump(all_metadata, json_file, indent=2)
#             print(f"Combined metadata written to {output_json_file}. Number of courses: {len(all_metadata)}")
#         except Exception as e:
#             print(f"Error writing JSON file: {e}")
#             exit(1)
#         # 3. Close the browser session
#         driver.quit()



#         # 4. Do something with the scraped results
#         #    e.g., print or store in JSON/CSV
#         # for item in all_course_data[:3]:  # show first few
#             # print(item)

#     except Exception as e:
#         print(f"Encountered an error: {e}")
#         driver.quit()


# if __name__ == "__main__":
#     main()

# import json

# with open("processed_links_cache.json", 'r', encoding='utf-8') as json_file:
#     data = json.load(json_file)
# print(len(data))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def scrape_udemy_courses():
    # Setup headless Chrome driver
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
        print("ChromeDriver successfully initialized.")
    except Exception as e:
        print("Error initializing ChromeDriver: %s", e)
        raise
    
    try:

        try:
            accept_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]"))
    )
            accept_button.click()
        except:
            print("No cookies")
            pass  # No banner or already accepted
        # Navigate to Udemy and click "Explore"
        driver.get("https://www.udemy.com/")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='popper-trigger--6']"))).click()
        print("Found Explore")
        # Collect categories and subcategories
        cat = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@id, 'header-browse-nav-category') and not(contains(., 'Certification preparation'))]")))
        categories = {}
        for cat_elem in cat:
            cat_name = cat_elem.text.strip()
            if cat_name:
                categories[cat_name] = []
                driver.get(cat_elem.get_attribute('href'))
                time.sleep(2)
                categories[cat_name] = [elem.text.strip() for elem in driver.find_elements(By.XPATH, "//a[contains(@class, 'subcategory')]") if elem.text.strip()]
        
        # Scrape courses for each category and subcategory
        all_courses = {}
        for category, subcategories in categories.items():
            all_courses[category] = {}
            for subcat in [category] + subcategories:  # Include category itself as a "subcategory"
                driver.get("https://www.udemy.com/")
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Explore')]"))).click()
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{category}') and not(contains(text(), 'Certificate'))]"))).click()
                if subcat != category:  # Click subcategory if it's not the main category
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{subcat}')]"))).click()
                time.sleep(3)  # Allow page to load
                courses = [elem.get_attribute('href') for elem in driver.find_elements(By.XPATH, "//a[contains(@class, 'course-card--course-title')]") if elem.get_attribute('href')]
                all_courses[category][subcat] = courses
                print(f"{category} - {subcat}: {len(courses)} courses")
        
        return all_courses
    
    finally:
        driver.quit()

if __name__ == "__main__":
    course_data = scrape_udemy_courses()