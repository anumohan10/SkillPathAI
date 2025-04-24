# scrapers/factory.py
from .udacity import UdacityScraper
from .coursera import CourseraScraper  # existing implementation
from .edx import EdxScraper
from .udemy import UdemyScraper

class ScraperFactory:
    @staticmethod
    def get_scraper(platform, driver):
        """
        Return an instance of a CourseScraper for the specified platform.
        """
        platform = platform.lower()
        if platform == "udacity":
            return UdacityScraper(driver, "https://www.udacity.com/catalog")
        elif platform == "coursera":
            return CourseraScraper(driver, "https://www.coursera.org/courses")
        elif platform == "edx":
            return EdxScraper(driver, "https://www.edx.org/search")
        elif platform == "udemy":
            return UdemyScraper(driver, "https://www.udemy.com/courses")
        else:
            raise ValueError(f"Unsupported platform: {platform}")
