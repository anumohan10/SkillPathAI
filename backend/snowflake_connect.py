import snowflake.connector

# # ✅ Update with the correct account identifier
# conn = snowflake.connector.connect(
#     user="DRAGON",
#     password="Skill@12345678",
#     account="https://pdb57018.snowflakecomputing.com",
#     warehouse="SKILLPATH_WH",
#     database="SKILLPATH_DB",
#     schema="RAW_DATA",
#     insecure_mode=True  
# )
 


conn = snowflake.connector.connect(
    user="DRAGON",
    password="Skill@12345678",
    account="sfedu02-pdb57018",
    warehouse="SKILLPATH_WH",
    database="SKILLPATH_DB",
    schema="RAW_DATA",
    )

cur = conn.cursor()
print("✅ Connected to Snowflake successfully!")

# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from bs4 import BeautifulSoup
# import time

# # Configure Chrome options
# chrome_options = Options()
# # Uncomment the next line to run in headless mode:
# # chrome_options.add_argument("--headless")
# chrome_options.add_argument("--start-maximized")
# chrome_options.add_argument("--no-sandbox")
# chrome_options.add_argument("--disable-dev-shm-usage")

# # Set up the ChromeDriver service with webdriver-manager
# service = Service(ChromeDriverManager().install())

# # Initialize the Chrome driver
# driver = webdriver.Chrome(service=service, options=chrome_options)

# # URL to scrape
# url = "https://www.coursera.org/courses?sortBy=BEST_MATCH"
# driver.get(url)

# # Wait for the dynamic content to load (adjust sleep as needed)
# time.sleep(5)

# # Get the rendered page source
# html = driver.page_source
# soup = BeautifulSoup(html, "html.parser")

# # Example: Find course listings (you may need to update the selectors if Coursera changes its layout)
# courses = soup.find_all("h3", class_="cds-CommonCard-title css-6ecy9b")
# print(f"Found {len(courses)} courses on the page.")
# print(courses)

# # # Print out course titles and links
# # for idx, course in enumerate(courses, 1):
# #     title_elem = course.find("h3")
# #     title = title_elem.get_text(strip=True) if title_elem else "No title found"
# #     link_elem = course.find("a", href=True)
# #     link = "https://www.coursera.org" + link_elem["href"] if link_elem else "No link found"
    
# #     print(f"{idx}. {title}")
# #     print(f"   Link: {link}")
# #     print("------")

# # Close the driver
# driver.quit()

# import time
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from bs4 import BeautifulSoup

# # Configure Chrome options (remove headless if you want to see the browser)
# chrome_options = Options()
# chrome_options.add_argument("--headless")
# chrome_options.add_argument("--no-sandbox")
# chrome_options.add_argument("--disable-dev-shm-usage")

# # Set up ChromeDriver using webdriver-manager
# service = Service(ChromeDriverManager().install())
# driver = webdriver.Chrome(service=service, options=chrome_options)

# # URL for the Google Data Analytics Professional Certificate page
# url = "https://www.coursera.org/professional-certificates/google-data-analytics"
# driver.get(url)

# # Wait for dynamic content to load; adjust sleep time if needed
# time.sleep(5)

# # Retrieve the page source and parse it with BeautifulSoup
# html = driver.page_source
# soup = BeautifulSoup(html, "html.parser")

# # Option 1: Print the entire text content of the page
# full_text = soup.get_text(separator="\n")
# print("----- Full Page Text -----")
# print(full_text)

# # Option 2: Extract specific sections (headings, paragraphs, and list items)
# print("\n----- Extracted Sections -----")
# for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li']):
#     text = element.get_text(strip=True)
#     if text:  # Only print non-empty text
#         print(text)

# driver.quit()

