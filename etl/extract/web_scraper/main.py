# main.py
import logging
from utils import create_headless_driver, save_json, load_processed_links, update_processed_links, retrieve_links
from scrapers.factory import ScraperFactory

def main():
    # Example: Change platform to "udacity", "coursera", or "edx" as needed.
    platform = "udacity"
    output_json_file = platform+"_course_metadata.json"
    cache_file = platform+"_processed_links_cache.json"
    
    scraper = ScraperFactory.get_scraper(platform, None)
    processed_links_cache = load_processed_links(cache_file)

    if platform == "udemy":
        links_df = retrieve_links(limit=10)
        num_pages_processed = scraper.process_catalog_pages(processed_links_cache, links_df,output_json_file)
        logging.info(f"Scraping completed. Total courses processed: {num_pages_processed}")

    else:
        driver = create_headless_driver()
        scraper.driver = driver
    # Loop through pages (adjust range as needed)
        for page in range(1,27):
            all_metadata = []
            page_metadata = scraper.process_catalog_page(page, processed_links_cache)
            for meta in page_metadata:
                all_metadata.append(meta)
        logging.info(f"Scraping completed. Total courses processed: {len(all_metadata)}" )

        update_processed_links(cache_file, processed_links_cache)
        save_json(all_metadata, output_json_file)
        driver.quit()
    

if __name__ == "__main__":
    main()
