# New file for dedicated learning path courses
import json
import logging
import pandas as pd
from backend.services.connection_pool import ConnectionPool

# Set up logger
logger = logging.getLogger(__name__)

def get_learning_path_courses(target_role, skill_ratings=None):
    """
    Get course recommendations specifically for learning paths
    with dedicated connections and error handling.
    
    Args:
        target_role (str): The target role
        skill_ratings (dict, optional): Dictionary of skill ratings
    
    Returns:
        pd.DataFrame: DataFrame with course recommendations
    """
    pool = ConnectionPool()
    conn = None
    cursor = None
    
    try:
        # Get a connection from the pool
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        # Create a safer version of target role for the query
        target_role = target_role.replace("'", "").replace('"', "")
        
        # Get missing skills or low-rated skills for query focus
        skill_query = ""
        
        # If skill ratings provided, focus on low-rated skills
        if skill_ratings:
            low_rated_skills = []
            for skill, rating in skill_ratings.items():
                rating_value = int(rating) if isinstance(rating, (str, int, float)) else 0
                if rating_value <= 2:  # Low rated skills are priorities
                    low_rated_skills.append(skill)
            
            if low_rated_skills:
                skill_focus = ', '.join(low_rated_skills[:3])  # Limit to top 3 for better search results
                skill_query = f" Focus on courses that teach {skill_focus}."
                logger.info(f"Adding skill focus to query: {skill_query}")
        
        # Use more direct search approach with additional logging
        logger.info(f"Getting courses for {target_role} with learning path dedicated service")
        query = f"""
        SELECT
          course.value:"COURSE_NAME"::string AS COURSE_NAME,
          course.value:"DESCRIPTION"::string AS DESCRIPTION,
          course.value:"SKILLS"::string AS SKILLS,
          course.value:"URL"::string AS URL,
          course.value:"LEVEL"::string AS LEVEL,
          course.value:"PLATFORM"::string AS PLATFORM,
          CASE
            WHEN LOWER(course.value:"LEVEL"::string) LIKE '%beginner%' THEN 'BEGINNER'
            WHEN LOWER(course.value:"LEVEL"::string) LIKE '%intermediate%' THEN 'INTERMEDIATE'
            WHEN LOWER(course.value:"LEVEL"::string) LIKE '%advanced%' THEN 'ADVANCED'
            WHEN LOWER(course.value:"LEVEL"::string) LIKE '%all%level%' 
              OR LOWER(course.value:"LEVEL"::string) LIKE '%all-level%' THEN 'ALL_LEVELS'
            ELSE 'INTERMEDIATE'
          END AS LEVEL_CATEGORY
        FROM
          TABLE(
            FLATTEN(
              INPUT => PARSE_JSON(
                SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                  'SKILLPATH_SEARCH_POC',
                  '{{
                    "query": "Show me the best courses for {target_role} including beginner, intermediate, and advanced levels.{skill_query}",
                    "columns": ["COURSE_NAME", "DESCRIPTION", "SKILLS", "URL", "LEVEL", "PLATFORM"],
                    "limit": 8
                  }}'
                )
              ):"results"
            )
          ) AS course
        WHERE
          course.value:"COURSE_NAME"::string IS NOT NULL
          AND course.value:"URL"::string IS NOT NULL
        """
        
        # Log the query for debugging
        logger.debug(f"Executing learning path search query")
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Process results
        if not rows:
            logger.warning("No course results returned from learning path query")
            return pd.DataFrame()
        
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        
        # Distribute ALL_LEVELS courses
        all_levels_courses = df[df['LEVEL_CATEGORY'] == 'ALL_LEVELS']
        if not all_levels_courses.empty:
            # Count how many we have in each category
            beginner_count = len(df[df['LEVEL_CATEGORY'] == 'BEGINNER'])
            intermediate_count = len(df[df['LEVEL_CATEGORY'] == 'INTERMEDIATE'])
            advanced_count = len(df[df['LEVEL_CATEGORY'] == 'ADVANCED'])
            
            # Create a copy to avoid modifying during iteration
            for index, course in all_levels_courses.iterrows():
                course_name = course.get('COURSE_NAME', '').lower()
                
                # Check for beginner/advanced indicators
                beginner_indicators = ["intro", "beginning", "basic", "fundamental", "foundation", "start"]
                advanced_indicators = ["advanced", "expert", "mastery", "professional", "master"]
                
                # First try to assign based on course name
                if any(word in course_name for word in beginner_indicators):
                    df.at[index, 'LEVEL_CATEGORY'] = 'BEGINNER'
                    beginner_count += 1
                elif any(word in course_name for word in advanced_indicators):
                    df.at[index, 'LEVEL_CATEGORY'] = 'ADVANCED'
                    advanced_count += 1
                else:
                    # Assign to category with fewest courses
                    if beginner_count <= intermediate_count and beginner_count <= advanced_count:
                        df.at[index, 'LEVEL_CATEGORY'] = 'BEGINNER'
                        beginner_count += 1
                    elif intermediate_count <= beginner_count and intermediate_count <= advanced_count:
                        df.at[index, 'LEVEL_CATEGORY'] = 'INTERMEDIATE'
                        intermediate_count += 1
                    else:
                        df.at[index, 'LEVEL_CATEGORY'] = 'ADVANCED'
                        advanced_count += 1
        
        logger.info(f"Found {len(df)} courses for learning path")
        return df
        
    except Exception as e:
        logger.error(f"Error getting learning path courses: {str(e)}", exc_info=True)
        return pd.DataFrame()
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                pool.release_connection(conn)
            except:
                pass

def get_fallback_courses_for_learning_path(target_role, skill_ratings=None):
    """
    Get fallback courses specifically for learning paths that won't
    conflict with career transition services.
    
    Args:
        target_role (str): Target role
        skill_ratings (dict, optional): Dictionary of skill ratings
    
    Returns:
        pd.DataFrame: DataFrame with fallback courses
    """
    try:
        # Log the fallback request
        logger.info(f"Using fallback courses for learning path: {target_role}")
        
        # Determine the domain based on the role
        role_lower = target_role.lower()
        
        # Determine skills to focus on
        focus_skills = []
        if skill_ratings:
            for skill, rating in skill_ratings.items():
                if int(rating) <= 2:
                    focus_skills.append(skill)
        
        # Determine the domain to create relevant generic courses
        if any(word in role_lower for word in ["data", "scientist", "analyst", "analytics"]):
            domain = "data science"
            domain_skills = "Python, Statistics, SQL, Data Visualization, Machine Learning"
            
        elif any(word in role_lower for word in ["finance", "financial", "accounting", "investment"]):
            domain = "finance"
            domain_skills = "Financial Analysis, Excel, Accounting, Financial Modeling"
            
        elif any(word in role_lower for word in ["software", "developer", "web", "frontend", "backend"]):
            domain = "software development"
            domain_skills = "Programming, Software Design, Testing, Version Control"
            
        elif any(word in role_lower for word in ["devops", "cloud", "infra", "infrastructure"]):
            domain = "devops"
            domain_skills = "Docker, Kubernetes, CI/CD, Cloud Infrastructure, Automation"
            
        elif any(word in role_lower for word in ["system", "systems", "infrastructure", "network"]):
            domain = "systems engineering"
            domain_skills = "Systems Design, Technical Documentation, Security, Cloud Computing"
            
        elif any(word in role_lower for word in ["design", "user", "ux", "ui"]):
            domain = "design"
            domain_skills = "Design Principles, User Experience, Visual Design, Prototyping"
            
        elif any(word in role_lower for word in ["market", "marketing", "sales", "business"]):
            domain = "marketing"
            domain_skills = "Marketing Strategy, Analytics, Market Research, Content Creation"
            
        else:
            # Very generic domain that works for any role
            domain = role.lower().split()[-1] if len(role.split()) > 0 else "professional"
            domain_skills = "Technical Skills, Communication, Problem Solving, Project Management"
            
        # Create generic courses with the appropriate role/domain
        courses = [
            # Beginner courses
            {
                "COURSE_NAME": f"Introduction to {target_role}",
                "DESCRIPTION": f"Learn the fundamental concepts and skills needed for a career as a {target_role}",
                "SKILLS": f"{domain_skills}",
                "URL": f"https://www.coursera.org/specializations/{domain.replace(' ', '-')}-fundamentals",
                "LEVEL": "Beginner",
                "PLATFORM": "Coursera",
                "LEVEL_CATEGORY": "BEGINNER"
            },
            {
                "COURSE_NAME": f"Essential {domain.title()} Skills",
                "DESCRIPTION": f"Master the core skills and tools required for entry-level {target_role} positions",
                "SKILLS": f"{domain_skills}",
                "URL": f"https://www.udemy.com/course/essential-{domain.replace(' ', '-')}-skills",
                "LEVEL": "Beginner",
                "PLATFORM": "Udemy",
                "LEVEL_CATEGORY": "BEGINNER"
            },
            
            # Intermediate courses
            {
                "COURSE_NAME": f"Intermediate {domain.title()} Concepts",
                "DESCRIPTION": f"Build on your foundational knowledge with more advanced concepts in {domain}",
                "SKILLS": f"Advanced {domain_skills}",
                "URL": f"https://www.edx.org/professional-certificate/{domain.replace(' ', '-')}",
                "LEVEL": "Intermediate",
                "PLATFORM": "edX",
                "LEVEL_CATEGORY": "INTERMEDIATE"
            },
            {
                "COURSE_NAME": f"Professional {target_role} Development",
                "DESCRIPTION": f"Enhance your capabilities as a {target_role} with industry-standard practices",
                "SKILLS": f"Professional {domain_skills}",
                "URL": f"https://www.coursera.org/professional-certificates/{domain.replace(' ', '-')}",
                "LEVEL": "Intermediate",
                "PLATFORM": "Coursera",
                "LEVEL_CATEGORY": "INTERMEDIATE"
            },
            
            # Advanced courses
            {
                "COURSE_NAME": f"Advanced {domain.title()} Specialization",
                "DESCRIPTION": f"Master advanced techniques and become an expert {target_role}",
                "SKILLS": f"Expert {domain_skills}, Leadership, Specialization",
                "URL": f"https://www.udemy.com/course/advanced-{domain.replace(' ', '-')}",
                "LEVEL": "Advanced",
                "PLATFORM": "Udemy",
                "LEVEL_CATEGORY": "ADVANCED"
            },
            {
                "COURSE_NAME": f"Expert {target_role} Masterclass",
                "DESCRIPTION": f"Learn cutting-edge approaches and techniques used by top professionals in {domain}",
                "SKILLS": f"Expert {domain_skills}, Innovation, Project Leadership",
                "URL": f"https://www.coursera.org/specializations/expert-{domain.replace(' ', '-')}",
                "LEVEL": "Advanced",
                "PLATFORM": "Coursera",
                "LEVEL_CATEGORY": "ADVANCED"
            }
        ]
        
        # Create a dataframe from the courses
        df = pd.DataFrame(courses)
        logger.info(f"Created {len(df)} fallback courses for learning path")
        
        return df
        
    except Exception as e:
        logger.error(f"Error creating fallback courses: {str(e)}")
        # Return an empty DataFrame on error
        return pd.DataFrame()