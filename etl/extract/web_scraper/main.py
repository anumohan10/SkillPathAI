# main.py
import logging
from utils import create_headless_driver, save_json, load_processed_links, update_processed_links
from scrapers.factory import ScraperFactory

def main():
    # Example: Change platform to "udacity", "coursera", or "edx" as needed.
    platform = "edx"
    output_json_file = platform+"_course_metadata.json"
    cache_file = platform+"_processed_links_cache.json"
    
    driver = create_headless_driver()
    scraper = ScraperFactory.get_scraper(platform, driver)
    all_metadata = []
    processed_links_cache = load_processed_links(cache_file)

    # Loop through pages (adjust range as needed)
    for page in range(1,42):
        page_metadata = scraper.process_catalog_page(page, processed_links_cache)
        for meta in page_metadata:
            all_metadata.append(meta)

    update_processed_links(cache_file, processed_links_cache)
    save_json(all_metadata, output_json_file)
    driver.quit()
    logging.info("Scraping completed. Total courses processed: %d", len(all_metadata))

if __name__ == "__main__":
    main()
