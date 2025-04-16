# File: backend/services/course_service.py
import json
import logging
import pandas as pd
from backend.database import get_snowflake_connection

# Set up logger
logger = logging.getLogger(__name__)

def get_course_recommendations(target_role, user_id=None, resume_id=None):
    """
    Get recommended courses using the Snowflake Cortex Search query with specific service,
    taking into account either skill ratings or missing skills from resume analysis.
    
    Args:
        target_role (str): The target role to get course recommendations for
        user_id (str/int, optional): The user ID to get skill ratings from learning path
        resume_id (str, optional): The resume ID to get missing skills from resume analysis
        
    Returns:
        DataFrame: A DataFrame containing course recommendations
    """
    logger.info(f"Getting recommended courses for role: {target_role}")
    
    conn = None
    cur = None
    
    try:
        logger.debug("Establishing Snowflake connection")
        conn = get_snowflake_connection()
        if not conn:
            logger.error("Failed to establish Snowflake connection")
            raise ConnectionError("Could not connect to Snowflake")
            
        cur = conn.cursor()
        
        # First, check what database and schema we're connected to
        logger.debug("Checking current database context")
        cur.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE();")
        db_context = cur.fetchone()
        logger.info(f"Connected to: Database={db_context[0]}, Schema={db_context[1]}, Role={db_context[2]}")
        
        # Use the SKILLPATH_SEARCH_POC service directly
        service_name = 'SKILLPATH_SEARCH_POC'
        logger.info(f"Using search service: {service_name}")
        
        # Get missing skills or low-rated skills for query focus
        skill_query = ""
        missing_skills = []
        
        # First try to get missing skills from resume if resume_id is provided
        if resume_id:
            try:
                logger.debug(f"Fetching missing skills from resume ID: {resume_id}")
                cur.execute(f"""
                SELECT 
                    TARGET_ROLE, MISSING_SKILLS
                FROM 
                    SKILLPATH_DB.PUBLIC.RESUMES 
                WHERE 
                    ID = '{resume_id}'
                """)
                
                result = cur.fetchone()
                if result and result[1]:  # Check if missing_skills exists and is not empty
                    # The first element is target_role, the second is missing_skills
                    missing_skills_data = result[1]
                    target_role_from_db = result[0]
                    
                    # If target_role is supplied by query param, override the database value
                    if not target_role and target_role_from_db:
                        target_role = target_role_from_db
                    
                    logger.debug(f"Found missing skills: {missing_skills_data}")
                    
                    # Handle different types of missing_skills (object or string)
                    try:
                        # If it's already a list, use it directly
                        if isinstance(missing_skills_data, list):
                            missing_skills = missing_skills_data
                        # If it's a string, try to parse it as JSON
                        elif isinstance(missing_skills_data, str):
                            missing_skills = json.loads(missing_skills_data)
                        else:
                            logger.warning(f"Unexpected missing_skills type: {type(missing_skills_data)}")
                            missing_skills = []
                        
                        if missing_skills:
                            skill_query = f" Focus on courses that teach {', '.join(missing_skills[:5])}."
                            logger.debug(f"Added missing skills focus to query: {skill_query}")
                    except Exception as e:
                        logger.error(f"Error processing missing skills: {e}")
                        # Continue without skill focus
            except Exception as e:
                logger.error(f"Error fetching missing skills from resume: {e}")
                # Continue without missing skills if there's an error
        
        # If no missing skills found and user_id is provided, try skill ratings approach as fallback
        if not missing_skills and user_id:
            try:
                logger.debug(f"Fetching skill ratings for user ID: {user_id}")
                cur.execute(f"""
                SELECT 
                    SKILL_RATINGS
                FROM 
                    SKILLPATH_DB.PROCESSED_DATA.LEARNING_PATHS 
                WHERE 
                    ID = '{user_id}'
                ORDER BY 
                    CREATED_AT DESC 
                LIMIT 1
                """)
                
                result = cur.fetchone()
                if result and result[0]:
                    skill_ratings = result[0]
                    logger.debug(f"Found skill ratings: {skill_ratings}")
                    
                    # Handle different types of skill_ratings (object or string)
                    try:
                        # If it's already a dictionary, use it directly
                        if isinstance(skill_ratings, dict):
                            ratings_dict = skill_ratings
                        # If it's a string, try to parse it as JSON
                        elif isinstance(skill_ratings, str):
                            ratings_dict = json.loads(skill_ratings)
                        else:
                            logger.warning(f"Unexpected skill_ratings type: {type(skill_ratings)}")
                            ratings_dict = {}
                            
                        # Find skills with low ratings (1-2) that need improvement
                        low_rated_skills = []
                        for skill, rating in ratings_dict.items():
                            rating_value = int(rating) if isinstance(rating, (str, int, float)) else 0
                            if rating_value <= 2:
                                low_rated_skills.append(skill)
                        
                        if low_rated_skills:
                            skill_query = f" Focus on courses that teach {', '.join(low_rated_skills)}."
                            logger.debug(f"Added skill focus to query: {skill_query}")
                    except Exception as e:
                        logger.error(f"Error processing skill ratings: {e}")
                        # Continue without skill focus
            except Exception as e:
                logger.error(f"Error fetching skill ratings: {e}")
                # Continue without skill ratings if there's an error
        
        # Set up a direct query to get course recommendations
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
            -- For "All Levels" courses, initially categorize them separately
            WHEN LOWER(course.value:"LEVEL"::string) LIKE '%all%level%' 
              OR LOWER(course.value:"LEVEL"::string) LIKE '%all-level%' THEN 'ALL_LEVELS'
            -- For other uncategorized courses, use ADVANCED as default
            ELSE 'ADVANCED'
          END AS LEVEL_CATEGORY
        FROM
          TABLE(
            FLATTEN(
              INPUT => PARSE_JSON(
                SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                  '{service_name}',
                  '{{
                    "query": "Show me the best courses for {target_role}s including beginner, intermediate, and advanced levels.{skill_query} Include detailed descriptions, skills covered, and URLs.",
                    "columns": ["COURSE_NAME", "DESCRIPTION", "SKILLS", "URL", "LEVEL", "PLATFORM"],
                    "limit": 6
                  }}'
                )
              ):"results"
            )
          ) AS course
        WHERE
          course.value:"COURSE_NAME"::string IS NOT NULL
          AND course.value:"DESCRIPTION"::string IS NOT NULL
          AND course.value:"URL"::string IS NOT NULL
        ORDER BY
          LEVEL_CATEGORY;
        """
        
        logger.debug(f"Executing search query with service {service_name}")
        cur.execute(query)
        logger.info(f"Query executed successfully with service {service_name}")
        
        # Fetch results
        rows = cur.fetchall()
        logger.info(f"Query returned {len(rows)} rows")
        
        if not rows:
            logger.error("Search query returned no results")
            raise ValueError("No course results returned from search query")
            
        columns = [desc[0] for desc in cur.description]
        
        # Create DataFrame from results
        df = pd.DataFrame(rows, columns=columns)
        
        # Check for valid data
        if df.empty:
            logger.error("Empty DataFrame after creating from query results")
            raise ValueError("No valid course data found")
        
        # Distribute "ALL_LEVELS" courses among BEGINNER, INTERMEDIATE, and ADVANCED
        all_levels_courses = df[df['LEVEL_CATEGORY'] == 'ALL_LEVELS']
        if not all_levels_courses.empty:
            logger.info(f"Distributing {len(all_levels_courses)} 'ALL_LEVELS' courses across difficulty levels")
            
            # Count how many we have in each category
            beginner_count = len(df[df['LEVEL_CATEGORY'] == 'BEGINNER'])
            intermediate_count = len(df[df['LEVEL_CATEGORY'] == 'INTERMEDIATE'])
            advanced_count = len(df[df['LEVEL_CATEGORY'] == 'ADVANCED'])
            
            # Create a copy to avoid modifying during iteration
            for index, course in all_levels_courses.iterrows():
                course_name = course.get('COURSE_NAME', '').lower()
                description = course.get('DESCRIPTION', '').lower()
                
                # Check for beginner indicators
                beginner_indicators = ["intro", "beginning", "basic", "fundamental", "foundation", "start"]
                advanced_indicators = ["advanced", "expert", "mastery", "professional", "master"]
                
                # First try to assign based on course name/description
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
            
            # Log the distribution
            logger.info(f"After distribution: BEGINNER={beginner_count}, INTERMEDIATE={intermediate_count}, ADVANCED={advanced_count}")
        
        # Log the data for debugging
        if not df.empty:
            logger.debug(f"First row of search data: {df.iloc[0].to_dict()}")
            # Log all rows for more comprehensive debugging
            for i, row in df.iterrows():
                logger.debug(f"Course {i+1}: {row.get('COURSE_NAME')} | URL: {row.get('URL')} | Level: {row.get('LEVEL_CATEGORY')}")
            
            # Clean up null values and ensure there are actual valid rows
            valid_courses = df[df['COURSE_NAME'].notna() & df['URL'].notna()]
            if valid_courses.empty and not df.empty:
                logger.warning("Query returned rows but no valid courses with both name and URL")
                
        return df
            
    except Exception as e:
        logger.error(f"Error in get_recommended_courses: {str(e)}", exc_info=True)
        raise  # Re-throw the exception to be handled by caller
    finally:
        if cur:
            try:
                cur.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass