import time
import random
import json
import logging
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base import CourseScraper
import re

class EdxScraper(CourseScraper):
    def get_catalog_url(self, page_number):
        """
        Build the edX catalog URL.
        Example: "https://www.edx.org/search?tab=course&page=2"
        """
        return f"https://www.edx.org/search?tab=course&language=English&page={page_number}"

    def get_course_links(self, catalog_url):
        """
        Extracts all course links from an edX search results page using Selenium.
        """
        logging.info("Loading catalog URL: %s", catalog_url)
        try:
            course_urls = set()
            self.driver.get(catalog_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "overflow-x-auto"))
            )
            time.sleep(2)
            # Find the outer div with class "overflow-x-auto"
            overflow_div = self.driver.find_element(By.CLASS_NAME, "overflow-x-auto")
            
            # Find the grid div inside it (class "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 py-4")
            grid_div = overflow_div.find_element(By.CLASS_NAME, "grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-3.gap-4.py-4")
            
            # Find all divs with class "flex justify-center" inside the grid
            course_divs = grid_div.find_elements(By.CLASS_NAME, "flex.justify-center")
            
            # Extract URLs from each course div
            for div in course_divs:
                try:
                    # Find the <a> tag within the div (assuming the link is in an <a> tag)
                    link = div.find_element(By.TAG_NAME, "a")
                    url = link.get_attribute("href")
                    if url:  # Ensure the URL exists
                        trimmed_url = re.sub(r'\?.*', '', url)
                        course_urls.add(trimmed_url)
                except Exception as e:
                    logging.error(f"Error extracting URL from a div on current page: {e}")
                    continue
            logging.info("Found %d course links on edX page.", len(course_urls))
            return course_urls
        except Exception as e:
            logging.error("Error loading catalog page (%s): %s", catalog_url, e)
        # try:
        #     logging.info("Loading catalog URL: %s", catalog_url)
        #     self.driver.get(catalog_url)
        #     time.sleep(3)  # Allow the page to load

        #     # Wait for the courses container to load
        #     WebDriverWait(self.driver, 10).until(
        #         EC.presence_of_element_located((By.CLASS_NAME, "overflow-x-auto"))
        #     )

        #     # Extract course links
        #     course_links = set()
        #     course_elements = self.driver.find_elements(By.CLASS_NAME, "flex.justify-center")
        #     for element in course_elements:
        #         try:
        #             link = element.find_element(By.TAG_NAME, "a").get_attribute("href")
        #             if link and "course" in link:
        #                 course_links.append(link)
        #         except Exception as e:
        #             logging.warning(f"Skipping a course due to error: {e}")

        #     logging.info("Found %d course links on edX page.", len(course_links))
        #     return list(set(course_links))  # Return unique URLs
        # except Exception as e:
        #     logging.error("Error loading catalog page (%s): %s", catalog_url, e)
        #     return list[course_links]

    def parse_course_page(self, course_url):
        """
        Fetches and returns the HTML source of an edX course page.
        """
        try:
            logging.info("Processing edX course URL: %s", course_url)
            self.driver.get(course_url)
            time.sleep(random.uniform(2, 4))  # Avoid detection
            return self.driver.page_source
        except Exception as e:
            logging.error("Error fetching course page (%s): %s", course_url, e)
            return None

    def extract_data(self, html_source):
        """
        Extracts course metadata using BeautifulSoup.
        """
        soup = BeautifulSoup(html_source, 'html.parser')
        course_data = {}

        print(f"Scraping - Page title: {soup.title.string if soup.title else 'No title found'}")
        
        #  URL from the meta tag**
        meta_url = soup.find('meta', {'property': 'og:url'})
        course_data["URL"] = meta_url.get('content') if meta_url else "Not found"

        # 1. Course Name (look for the main course title, typically in an h1)
        try:
            course_name = soup.find('h1', class_=lambda x: x and any(c in x for c in ['tracking-tight', 'font-bold', 'text-2xl']))
            course_data["course_name"] = course_name.text.strip() if course_name else "Not found"
        except:
            print(f"Course name not found")
            course_data["course_name"] = "Not found"

        # 2. Institution (prioritize JSON-LD, fallback to HTML "At a Glance" section)
        try:
            # Try JSON-LD first (look for provider.name, handling provider as an array)
            script_tag = soup.find("script", type="application/ld+json")
            if script_tag:
                json_data = json.loads(script_tag.string)
                providers = json_data.get("provider", [])
                if isinstance(providers, list) and providers:
                    # Extract name from the first provider object of type CollegeOrUniversity
                    for provider in providers:
                        if isinstance(provider, dict) and provider.get("@type") == "CollegeOrUniversity":
                            institution = provider.get("name", "Not found")
                            if institution != "Not found":
                                course_data["institution"] = institution
                                break
                    else:
                        course_data["institution"] = "Not found"
                else:
                    # Handle if provider is a single object (not an array)
                    institution = json_data.get("provider", {}).get("name", "Not found")
                    course_data["institution"] = institution if institution != "Not found" else "Not found"
            else:
                # Fallback to HTML in "At a Glance" section under "Institution"
                institution = soup.find('li', class_='AtAGlance_parsed__AaBsT').find('span', class_='font-bold mr-1', string='Institution').find_next('a', class_='pointer text-black-100 underline').text.strip()
                course_data["institution"] = institution if institution else "Not found"
        except:
            print(f"Institution not found")
            course_data["institution"] = "Not found"

        # 3. Course Description (look for description in the main content or prose sections)
        try:
            description = soup.find('div', class_=['md:[&_p]:text-lg', 'prose']) or soup.find('p', class_='text-gray-800')
            if not description:
                description = soup.find('div', class_='contentHero_contentHero__CkUd6').find('p', class_='text-gray-800')
            course_data["course_description"] = description.text.strip() if description and description.text.strip() else "Not found"
        except:
            print(f"Course description not found")
            course_data["course_description"] = "Not found"

        # 4. Level (prioritize JSON-LD, fallback to HTML "At a Glance" section)
        try:
            # Try JSON-LD first
            script_tag = soup.find("script", type="application/ld+json")
            if script_tag:
                json_data = json.loads(script_tag.string)
                course_data["level"] = json_data.get("educationalLevel", "Not found").capitalize() if json_data.get("educationalLevel") else "Not found"
            else:
                # Fallback to HTML in "At a Glance" section
                level = soup.find('li', class_='AtAGlance_parsed__AaBsT').find('span', class_='font-bold', string='Level').find_next('span').text.strip()
                course_data["level"] = level if level else "Not found"
        except:
            print(f"Level not found")
            course_data["level"] = "Not found"

        
        # 5. Duration (prioritize JSON-LD, fallback to HTML course details grid or "At a Glance" section)
        try:
            script_tag = soup.find("script", type="application/ld+json")
            if script_tag:
                json_data = json.loads(script_tag.string)
                # Try timeRequired first (assuming it's in weeks, e.g., "5" means 5 weeks)
                time_required = json_data.get("timeRequired", "Not found")
                if time_required != "Not found" and isinstance(time_required, (str, int)):
                    if isinstance(time_required, str) and "PT" in time_required:
                        # Handle ISO 8601 duration (e.g., "PT13H" for hours, but we want weeks)
                        duration_weeks = "Not found"
                    else:
                        # Assume timeRequired is the number of weeks (e.g., "5" -> "5 weeks")
                        duration_weeks = f"{time_required} weeks" if str(time_required).isdigit() else "Not found"
                else:
                    # Fallback to hasCourseInstance.courseSchedule.repeatCount for weeks
                    course_instance = json_data.get("hasCourseInstance", [])
                    if isinstance(course_instance, list) and course_instance:
                        for instance in course_instance:
                            if isinstance(instance, dict):
                                schedule = instance.get("courseSchedule", {})
                                if isinstance(schedule, dict):
                                    repeat_count = schedule.get("repeatCount", "Not found")
                                    if repeat_count != "Not found" and isinstance(repeat_count, (int, str)) and str(repeat_count).isdigit():
                                        duration_weeks = f"{repeat_count} weeks"
                                        break
                    duration_weeks = duration_weeks if "weeks" in duration_weeks else "Not found"

                course_data["duration"] = duration_weeks if duration_weeks != "Not found" else "Not found"
            else:
                course_data["duration"] = "Not found"
        except:
            print(f"Duration not found for page")
            course_data["duration"] = "Not found"

        # 7. Rating (look for rating in the aria-label, rating display, JSON-LD aggregateRating, or new HTML structure)
        try:
            script_tag = soup.find("script", type="application/ld+json")
            if script_tag:
                json_data = json.loads(script_tag.string)
                rating = json_data.get("aggregateRating", {}).get("ratingValue", "Not found")
                course_data["rating"] = str(rating) if rating != "Not found" else "Not found"
            else:
                course_data["rating"] = "Not found"
        except:
            print(f"Rating not found for page")
            course_data["rating"] = "Not found"

       
    # 11. Associated skills (prioritize JSON-LD "about" for skills, fallback to HTML "At a Glance" section)
        try:
            script_tag = soup.find("script", type="application/ld+json")
            if script_tag:
                json_data = json.loads(script_tag.string)
                skills = json_data.get("about", "Not found")
                if skills != "Not found":
                    if isinstance(skills, list):
                        # Extract the "skill" values from the "about" objects, filter, and join into a comma-separated string
                        skill_names = [item.get("skill", "").strip() for item in skills if isinstance(item, dict) and item.get("skill")]
                        filtered_skills = [skill for skill in skill_names if skill and not any(unwanted in skill.lower() for unwanted in ['learn', 'search', 'popular', 'business', 'trending', 'view', 'results', 'better', 'futures', 'international', 'women', 'day', 'code', 'close', 'site', 'banner'])]
                        course_data["associated_skills"] = ", ".join(filtered_skills) if filtered_skills else "Not found"
                    else:
                        course_data["associated_skills"] = "Not found"
                else:
                    course_data["associated_skills"] = "Not found"
            else:
                course_data["associated_skills"] = "Not found"
        except:
            print(f"Associated skills not found for page")
            course_data["associated_skills"] = "Not found"
        
        # 10. Grow these skills 
        try:
            script_tag = soup.find("script", type="application/ld+json")
            if script_tag:
                json_data = json.loads(script_tag.string)
                skills = json_data.get("skills", json_data.get("teaches", "Not found"))
                if skills != "Not found":
                    if isinstance(skills, list):
                        # Filter and join the list of skills into a comma-separated string
                        filtered_skills = [skill.strip() for skill in skills if skill and not any(unwanted in str(skill).lower() for unwanted in ['learn', 'search', 'popular', 'business', 'trending', 'view', 'results', 'better', 'futures', 'international', 'women', 'day', 'code', 'close', 'site', 'banner'])]
                        course_data["grow_these_skills"] = ", ".join(filtered_skills) if filtered_skills else "Not found"
                    else:
                        # Handle if skills is a string (e.g., comma-separated)
                        skills_text = str(skills).strip()
                        skills_list = [skill.strip() for skill in skills_text.split(',')]
                        filtered_skills = [skill for skill in skills_list if skill and not any(unwanted in skill.lower() for unwanted in ['learn', 'search', 'popular', 'business', 'trending', 'view', 'results', 'better', 'futures', 'international', 'women', 'day', 'code', 'close', 'site', 'banner'])]
                        course_data["grow_these_skills"] = ", ".join(filtered_skills) if filtered_skills else "Not found"
                else:
                    course_data["grow_these_skills"] = "Not found"
            else:
                course_data["grow_these_skills"] = "Not found"
        except:
            print(f"Grow these skills not found for page")
            course_data["grow_these_skills"] = "Not found"

        # 11. Prerequisites (prioritize JSON-LD, fallback to HTML "At a Glance" section)
        try:
            # Try JSON-LD first (coursePrerequisites)
            script_tag = soup.find("script", type="application/ld+json")
            if script_tag:
                json_data = json.loads(script_tag.string)
                prerequisites = json_data.get("coursePrerequisites", ["Not found"])
                course_data["prerequisites"] = prerequisites[0] if prerequisites and prerequisites[0] != "Not found" else "Not found"
            else:
                # Fallback to HTML in "At a Glance" section
                prerequisites = soup.find('li', class_='AtAGlance_parsed__AaBsT').find('span', class_='font-bold', string='Prerequisites').find_next('p').text.strip()
                course_data["prerequisites"] = prerequisites if prerequisites else "Not found"
        except:
            print(f"Prerequisites not found for page")
            course_data["prerequisites"] = "Not found"

        # 12. Language (prioritize JSON-LD, fallback to HTML "At a Glance" section)
        try:
            # Try JSON-LD first (inLanguage or availableLanguage)
            script_tag = soup.find("script", type="application/ld+json")
            if script_tag:
                json_data = json.loads(script_tag.string)
                language = json_data.get("inLanguage", json_data.get("availableLanguage", "Not found"))
                course_data["language"] = language if language != "Not found" else "Not found"
            else:
                # Fallback to HTML in "At a Glance" section
                language = soup.find('li', class_='AtAGlance_parsed__AaBsT').find('span', class_='font-bold', string='Language').find_next('span').text.strip()
                course_data["language"] = language if language else "Not found"
        except:
            print(f"Language not found for page")
            course_data["language"] = "Not found"
            
        # 13. Price
        course_data["price"] = "$199.2"

        return course_data
